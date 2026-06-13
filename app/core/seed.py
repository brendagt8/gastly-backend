"""Datos iniciales del catálogo. Solo se insertan si las tablas están vacías;
después de eso la BD es la fuente de verdad y se edita directamente ahí."""
from sqlalchemy import select, func
from app.core.database import AsyncSessionLocal
from app.models.category import Category
from app.models.bank_sender import BankSender

DEFAULT_CATEGORIES = [
    dict(id="despensa", label="Despensa", emoji="🛒", color="#3ECF8E", default_budget=3000, sort_order=1,
         description="supermercados, tiendas de abarrotes, OXXO, Walmart, HEB, Soriana, Chedraui",
         keywords="HEB,WALMART,SORIANA,CHEDRAUI,OXXO,SEVEN,SUPER,MERCADO,BODEGA"),
    dict(id="salidas", label="Salidas", emoji="🍽️", color="#FFB547", default_budget=2000, sort_order=2,
         description="restaurantes, cafeterías, bares, comida rápida, antros, entretenimiento",
         keywords="STARBUCKS,MCDONALD,DOMINO,PIZZA,RESTAURANT,SUSHI,TACO,BURGER,KFC"),
    dict(id="gasolina", label="Gasolina", emoji="⛽", color="#5B9CF6", default_budget=1500, sort_order=3,
         description="gasolineras, estacionamientos, casetas, Uber/Didi si es transporte",
         keywords="PEMEX,TOTAL GAS,GASOLINERA,BP,SHELL,G500"),
    dict(id="salud", label="Salud", emoji="💊", color="#FF6B6B", default_budget=1000, sort_order=4,
         description="farmacias, hospitales, clínicas, médicos, laboratorios, ópticas",
         keywords="FARMACIA,GUADALAJARA,SIMILARES,BENAVIDES,HOSPITAL,CLINICA,DR ,DRA "),
    dict(id="suscripciones", label="Suscripciones", emoji="📱", color="#B57BFF", default_budget=500, sort_order=5,
         description="Netflix, Spotify, Disney+, HBO, Amazon Prime, servicios digitales mensuales",
         keywords="NETFLIX,SPOTIFY,DISNEY,HBO,AMAZON PRIME,APPLE,GOOGLE ONE,YOUTUBE"),
    dict(id="ropa", label="Ropa", emoji="👗", color="#FF6B6B", default_budget=2000, sort_order=6,
         description="tiendas de ropa, zapaterías, Zara, H&M, Nike, Adidas",
         keywords="ZARA,H&M,NIKE,ADIDAS,PULL&BEAR,STRADIVARIUS,BERSHKA"),
    dict(id="skincare", label="Skincare", emoji="🧴", color="#F472B6", default_budget=1000, sort_order=7,
         description="productos y tiendas de cuidado facial y corporal, Sephora, The Body Shop, cremas, sueros, protector solar, maquillaje",
         keywords="SEPHORA,BODY SHOP,CERAVE,NEUTROGENA,CLINIQUE,LANCOME,KIEHLS,FENTY,ULTA,BEAUTYBAY,SKINCEUTICALS"),
    dict(id="otros", label="Otros", emoji="📦", color="#6B7280", default_budget=1000, sort_order=8,
         description="todo lo que no encaje en las categorías anteriores",
         keywords=""),
]

DEFAULT_BANK_SENDERS = [
    dict(email="alertas@notificaciones.santander.com.mx", parser_key="santander"),
    dict(email="notificaciones@bbva.com", parser_key="bbva"),
    dict(email="notificacoes@nubank.com.br", parser_key="nu"),
    dict(email="alertas@banorte.com", parser_key="banorte"),
    dict(email="americanexpress@welcome.aexp.com", parser_key="amex"),
    dict(email="americanexpressmexico@welcome.aexp.com", parser_key="amex"),
    dict(email="noreply@americanexpress.com", parser_key="amex"),
]


async def seed_defaults():
    async with AsyncSessionLocal() as db:
        if (await db.execute(select(func.count(Category.id)))).scalar() == 0:
            for c in DEFAULT_CATEGORIES:
                db.add(Category(**c))
        if (await db.execute(select(func.count(BankSender.id)))).scalar() == 0:
            for s in DEFAULT_BANK_SENDERS:
                db.add(BankSender(**s))
        await db.commit()
