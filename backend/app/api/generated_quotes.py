"""
API Devis Générés - À implémenter.

Endpoints prévus:
- GET    /generated-quotes           : Liste des devis
- GET    /generated-quotes/{id}      : Détail d'un devis
- POST   /generated-quotes           : Création
- POST   /generated-quotes/{id}/generate-pdf : Génération PDF
- POST   /generated-quotes/{id}/send : Envoi par email
- PATCH  /generated-quotes/{id}/status : Mise à jour du statut
"""
from fastapi import APIRouter

router = APIRouter()


# TODO: Implémenter les endpoints de gestion des devis
