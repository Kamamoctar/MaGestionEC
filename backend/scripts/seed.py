"""
Script de seed : initialise la base avec un premier admin, une direction et un poste.
Usage : python scripts/seed.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.config import settings
from app.database import Base
from app.models.utilisateur import Utilisateur, RoleFonctionnel
from app.models.tenant import Tenant, TenantMembre
from app.models.direction import Direction
from app.models.poste import Poste, NiveauAcces
from app.models.poste_affectation import PosteAffectation, TypeAffectation
from app.core.security import hash_password

import uuid
from datetime import datetime, timezone


async def seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with Session() as db:
        tenant_result = await db.execute(select(Tenant).where(Tenant.slug == "gec-demo"))
        tenant = tenant_result.scalar_one_or_none()
        if tenant is None:
            tenant = Tenant(nom="GEC Demo", slug="gec-demo")
            db.add(tenant)
            await db.flush()

        async def ensure_membre(user: Utilisateur, role: RoleFonctionnel):
            membre_result = await db.execute(
                select(TenantMembre).where(
                    TenantMembre.tenant_id == tenant.id,
                    TenantMembre.utilisateur_id == user.id,
                )
            )
            if membre_result.scalar_one_or_none() is None:
                db.add(TenantMembre(
                    tenant_id=tenant.id,
                    utilisateur_id=user.id,
                    role_fonctionnel=role,
                ))

        # Admin
        existing = await db.execute(select(Utilisateur).where(Utilisateur.email == "admin@gec.local"))
        existing_admin = existing.scalar_one_or_none()
        if existing_admin:
            await ensure_membre(existing_admin, RoleFonctionnel.admin)
            existing_sec = await db.execute(select(Utilisateur).where(Utilisateur.email == "secretariat@gec.local"))
            sec_user = existing_sec.scalar_one_or_none()
            if sec_user:
                await ensure_membre(sec_user, RoleFonctionnel.secretariat)
            await db.commit()
            print("Seed déjà effectué — appartenances tenant vérifiées.")
            return

        admin = Utilisateur(
            nom="Admin",
            prenom="GEC",
            email="admin@gec.local",
            password_hash=hash_password("Admin1234!"),
            role_fonctionnel=RoleFonctionnel.admin,
        )
        db.add(admin)
        await db.flush()
        await ensure_membre(admin, RoleFonctionnel.admin)

        # Direction
        dg = Direction(nom="Direction Générale", description="Direction principale", tenant_id=tenant.id)
        db.add(dg)
        await db.flush()

        # Poste
        poste_dg = Poste(
            intitule="Directeur Général",
            tenant_id=tenant.id,
            direction_id=dg.id,
            occupant_user_id=admin.id,
            niveau_acces=NiveauAcces.confidentiel,
        )
        db.add(poste_dg)
        await db.flush()

        # Affectation initiale
        affectation = PosteAffectation(
            poste_id=poste_dg.id,
            utilisateur_id=admin.id,
            date_debut=datetime.now(timezone.utc),
            type=TypeAffectation.titulaire,
        )
        db.add(affectation)

        # Utilisateur secrétariat de démo
        sec = Utilisateur(
            nom="Diallo",
            prenom="Aminata",
            email="secretariat@gec.local",
            password_hash=hash_password("Secret1234!"),
            role_fonctionnel=RoleFonctionnel.secretariat,
        )
        db.add(sec)
        await db.flush()
        await ensure_membre(sec, RoleFonctionnel.secretariat)

        # Poste secrétariat
        poste_sec = Poste(
            intitule="Secrétariat Général",
            tenant_id=tenant.id,
            direction_id=dg.id,
            occupant_user_id=sec.id,
            niveau_acces=NiveauAcces.normal,
        )
        db.add(poste_sec)
        await db.flush()

        db.add(PosteAffectation(
            poste_id=poste_sec.id,
            utilisateur_id=sec.id,
            date_debut=datetime.now(timezone.utc),
            type=TypeAffectation.titulaire,
        ))

        await db.commit()

    print("Seed OK !")
    print("  Admin      : admin@gec.local      / Admin1234!")
    print("  Secrétariat: secretariat@gec.local / Secret1234!")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
