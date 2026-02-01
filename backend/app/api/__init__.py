from fastapi import APIRouter
from app.api import partners, quotes, imports, matching, customers, generated_quotes, cities, customer_quotes

api_router = APIRouter()

api_router.include_router(partners.router, prefix="/partners", tags=["Partenaires"])
api_router.include_router(quotes.router, prefix="/quotes", tags=["Tarifs"])
api_router.include_router(imports.router, prefix="/imports", tags=["Imports"])
api_router.include_router(matching.router, prefix="/match", tags=["Matching"])
api_router.include_router(customers.router, prefix="/customers", tags=["Clients"])
api_router.include_router(generated_quotes.router, prefix="/generated-quotes", tags=["Devis"])
api_router.include_router(cities.router, prefix="/cities", tags=["Villes"])
api_router.include_router(customer_quotes.router, prefix="/customer-quotes", tags=["Devis Client (Panier)"])
