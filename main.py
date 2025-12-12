from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from bson import ObjectId

from database import db, org_collection, admin_collection, get_org_collection_name
from models import (
    OrgCreateRequest,
    OrgUpdateRequest,
    OrgDeleteRequest,
    OrgResponse,
    AdminLoginRequest,
    TokenResponse,
)
from auth import hash_password, verify_password, create_access_token
from config import JWT_SECRET_KEY, JWT_ALGORITHM

app = FastAPI(title="Organization Management Service")

security = HTTPBearer()


# ----------------- Basic & DB check -----------------


@app.get("/")
async def root():
    return {"message": "Backend assignment app is running!"}


@app.get("/db-check")
async def db_check():
    try:
        collections = await db.list_collection_names()
        return {"status": "MongoDB Connected", "collections": collections}
    except Exception as e:
        return {"status": "Failed to connect DB", "error": str(e)}


# ----------------- Auth helper -----------------


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Reads JWT token, finds admin in DB, returns admin document."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub")
        org_id: str = payload.get("org_id")

        if email is None or org_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    admin = await admin_collection.find_one(
        {"email": email, "organization_id": org_id}
    )
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin not found",
        )

    return admin


# ----------------- 1. Create Organization -----------------

from fastapi import FastAPI, HTTPException, Depends, status
# ... (rest of your imports stay same)


@app.post("/org/create", response_model=OrgResponse)
async def create_organization(payload: OrgCreateRequest):
    org_name = payload.organization_name.strip()

    if not org_name:
        raise HTTPException(
            status_code=400,
            detail="Organization name cannot be empty",
        )

    try:
        # Check if org already exists
        existing = await org_collection.find_one({"organization_name": org_name})
        if existing:
            raise HTTPException(status_code=400, detail="Organization already exists")

        # Collection name for this org
        collection_name = get_org_collection_name(org_name)

        # Insert org into master organizations collection
        org_doc = {
            "organization_name": org_name,
            "collection_name": collection_name,
        }
        org_result = await org_collection.insert_one(org_doc)
        org_id = str(org_result.inserted_id)

        # Create admin user with hashed password
        admin_doc = {
            "email": payload.email,
            "password_hash": hash_password(payload.password),
            "organization_id": org_id,
        }
        await admin_collection.insert_one(admin_doc)

        # touch org collection
        org_specific_collection = db[collection_name]
        await org_specific_collection.insert_one({"_init": True})
        await org_specific_collection.delete_one({"_init": True})

        return OrgResponse(
            organization_name=org_name,
            collection_name=collection_name,
            admin_email=payload.email,
        )

    except HTTPException:
        # re-raise normal HTTP errors (like 400)
        raise
    except Exception as e:
        # print full stack in terminal
        import traceback
        traceback.print_exc()
        # send the error message back in response so we can see it in Swagger
        raise HTTPException(
            status_code=500,
            detail=f"Internal error in /org/create: {e}",
        )



# ----------------- 2. Get Organization -----------------


@app.get("/org/get", response_model=OrgResponse)
async def get_organization(organization_name: str):
    org = await org_collection.find_one({"organization_name": organization_name})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    admin = await admin_collection.find_one(
        {"organization_id": str(org["_id"])}
    )
    admin_email = admin["email"] if admin else "unknown"

    return OrgResponse(
        organization_name=org["organization_name"],
        collection_name=org["collection_name"],
        admin_email=admin_email,
    )


# ----------------- 3. Admin Login -----------------


@app.post("/admin/login", response_model=TokenResponse)
async def admin_login(payload: AdminLoginRequest):
    admin = await admin_collection.find_one({"email": payload.email})
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(payload.password, admin["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Get org for this admin
    org = await org_collection.find_one(
        {"_id": ObjectId(admin["organization_id"])}
    )
    if not org:
        raise HTTPException(
            status_code=500,
            detail="Organization not found for this admin",
        )

    token_data = {
        "sub": admin["email"],
        "org_id": admin["organization_id"],
        "org_name": org["organization_name"],
    }
    access_token = create_access_token(token_data)

    return TokenResponse(access_token=access_token)


# ----------------- 4. Update Organization -----------------


@app.put("/org/update")
async def update_organization(
    payload: OrgUpdateRequest,
    current_admin: dict = Depends(get_current_admin),
):
    old_name = payload.old_organization_name.strip()
    new_name = payload.new_organization_name.strip()

    if not new_name or old_name == new_name:
        raise HTTPException(
            status_code=400,
            detail="New organization name must be different and not empty",
        )

    # Get current org
    org = await org_collection.find_one({"organization_name": old_name})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Ensure this admin belongs to this org
    if str(org["_id"]) != current_admin["organization_id"]:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to update this organization",
        )

    # Check if new name already taken
    existing_new = await org_collection.find_one({"organization_name": new_name})
    if existing_new:
        raise HTTPException(
            status_code=400,
            detail="New organization name already exists",
        )

    old_collection_name = org["collection_name"]
    new_collection_name = get_org_collection_name(new_name)

    old_coll = db[old_collection_name]
    new_coll = db[new_collection_name]

    # Copy data from old collection to new one
    cursor = old_coll.find({})
    async for doc in cursor:
        doc["_id"] = ObjectId()  # new id
        await new_coll.insert_one(doc)

    # Drop old collection
    await old_coll.drop()

    # Update org master document
    await org_collection.update_one(
        {"_id": org["_id"]},
        {
            "$set": {
                "organization_name": new_name,
                "collection_name": new_collection_name,
            }
        },
    )

    # Optionally update admin email/password if provided
    update_admin_fields = {}
    if payload.email is not None:
        update_admin_fields["email"] = payload.email
    if payload.password is not None:
        update_admin_fields["password_hash"] = hash_password(payload.password)

    if update_admin_fields:
        await admin_collection.update_many(
            {"organization_id": str(org["_id"])},
            {"$set": update_admin_fields},
        )

    return {"message": "Organization updated successfully"}


# ----------------- 5. Delete Organization -----------------


@app.delete("/org/delete")
async def delete_organization(
    payload: OrgDeleteRequest,
    current_admin: dict = Depends(get_current_admin),
):
    organization_name = payload.organization_name.strip()

    org = await org_collection.find_one({"organization_name": organization_name})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Ensure this admin belongs to this org
    if str(org["_id"]) != current_admin["organization_id"]:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to delete this organization",
        )

    # Drop org-specific collection
    coll_name = org["collection_name"]
    await db[coll_name].drop()

    # Delete all admins for this org
    await admin_collection.delete_many({"organization_id": str(org["_id"])})

    # Delete org from master collection
    await org_collection.delete_one({"_id": org["_id"]})

    return {"message": "Organization deleted successfully"}
