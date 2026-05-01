from shared.models.prediction import PredictionAlert
from shared.models.info_config import ConfigStats
from shared.models.user import User
from datetime import date

class MockBackendService:
    def get_alerts(self) -> list[PredictionAlert]:
        return [
            PredictionAlert(
                product_name="Premium Cola",
                barcode="7501000123456",
                category="Bebidas",
                image_url="https://www.coca-cola.com/content/dam/onexp/co/es/brands/coca-cola/coca-cola-original/ccso_600ml_750x750.png",
                objective_date=date(2026, 4, 10),
                prediction=25,
                avg_weekly_sales=22.0,
                type="deficit",
                feature=True,
            ),
            
            PredictionAlert(
                product_name="Gansito",
                barcode="7501000152056",
                category="Postre",
                image_url="https://ayala-amaya-online.myshopify.com/cdn/shop/products/GANSITO50GR_dc4d79db-ad9c-443e-a4ea-70a2456d11fe_300x300.png?v=1595429786",
                objective_date=date(2026, 4, 10),
                prediction=17,
                avg_weekly_sales=25.0,
                type="superavit",
                feature=True,
            ),
            
            PredictionAlert(
                product_name="Príncipes",
                barcode="7741500152056",
                category="Galletas",
                image_url="https://marinelausa.com/sites/default/files/styles/large/public/2023-03/Principe%20Chocolate%208%20ct%20SS_0.png.webp?itok=kUSOkOjb",
                objective_date=date(2026, 4, 10),
                prediction=17,
                avg_weekly_sales=18,
                type="none",
                feature=False,
            ),             

            PredictionAlert(
                product_name="Doritos",
                barcode="7741500152056",
                category="Galletas",
                image_url="https://farmaciacalderon.com/cdn/shop/products/705419014010_1200x1200.png?v=1605548643",
                objective_date=date(2026, 4, 10),
                prediction=17,
                avg_weekly_sales=18,
                type="none",
                feature=False,
            ),   

            PredictionAlert(
                product_name="Doritos",
                barcode="7741500152056",
                category="Galletas",
                image_url="https://farmaciacalderon.com/cdn/shop/products/705419014010_1200x1200.png?v=1605548643",
                objective_date=date(2026, 4, 10),
                prediction=17,
                avg_weekly_sales=18,
                type="none",
                feature=False,
            ), 

            PredictionAlert(
                product_name="Doritos",
                barcode="7741500152056",
                category="Galletas",
                image_url="https://farmaciacalderon.com/cdn/shop/products/705419014010_1200x1200.png?v=1605548643",
                objective_date=date(2026, 4, 10),
                prediction=17,
                avg_weekly_sales=18,
                type="none",
                feature=False,
            ), 

            PredictionAlert(
                product_name="Doritos",
                barcode="7741500152056",
                category="Galletas",
                image_url="https://farmaciacalderon.com/cdn/shop/products/705419014010_1200x1200.png?v=1605548643",
                objective_date=date(2026, 4, 10),
                prediction=17,
                avg_weekly_sales=18,
                type="none",
                feature=False,
            ), 

            PredictionAlert(
                product_name="Doritos",
                barcode="7741500152056",
                category="Galletas",
                image_url="https://farmaciacalderon.com/cdn/shop/products/705419014010_1200x1200.png?v=1605548643",
                objective_date=date(2026, 4, 10),
                prediction=17,
                avg_weekly_sales=18,
                type="none",
                feature=False,
            ), 

            PredictionAlert(
                product_name="Doritos",
                barcode="7741500152056",
                category="Galletas",
                image_url="https://farmaciacalderon.com/cdn/shop/products/705419014010_1200x1200.png?v=1605548643",
                objective_date=date(2026, 4, 10),
                prediction=17,
                avg_weekly_sales=18,
                type="none",
                feature=False,
            ), 

            PredictionAlert(
                product_name="Doritos",
                barcode="7741500152056",
                category="Galletas",
                image_url="https://farmaciacalderon.com/cdn/shop/products/705419014010_1200x1200.png?v=1605548643",
                objective_date=date(2026, 4, 10),
                prediction=17,
                avg_weekly_sales=18,
                type="none",
                feature=False,
            ), 

            PredictionAlert(
                product_name="Doritos",
                barcode="7741500152056",
                category="Galletas",
                image_url="https://farmaciacalderon.com/cdn/shop/products/705419014010_1200x1200.png?v=1605548643",
                objective_date=date(2026, 4, 10),
                prediction=17,
                avg_weekly_sales=18,
                type="none",
                feature=False,
            ),        
        ]
    
    def get_alerts_prob(self) -> list[PredictionAlert]:
        return [
            PredictionAlert(
                product_name="Premium Cola",
                barcode="7501000123456",
                category="Bebidas",
                image_url="https://www.coca-cola.com/content/dam/onexp/co/es/brands/coca-cola/coca-cola-original/ccso_600ml_750x750.png",
                objective_date=date(2026, 4, 10),
                prediction=25,
                avg_weekly_sales=22.0,
                type="deficit",
                feature=True,
            ),
            
            PredictionAlert(
                product_name="Gansito",
                barcode="7501000152056",
                category="Postre",
                image_url="https://ayala-amaya-online.myshopify.com/cdn/shop/products/GANSITO50GR_dc4d79db-ad9c-443e-a4ea-70a2456d11fe_300x300.png?v=1595429786",
                objective_date=date(2026, 4, 10),
                prediction=17,
                avg_weekly_sales=25.0,
                type="superavit",
                feature=True,
            ),]

    def get_dashboard_stats(self) -> dict:
        return {
            "total_scans_today": 1247,
            "active_predictions": 23,
            "pending_syncs": 8,
            "is_online": True,
        }
        
    def get_product_detail(self, barcode: str) -> PredictionAlert:
        return PredictionAlert(
            product_name="Príncipes",
            barcode="7741500152056",
            category="Galletas",
            image_url="https://marinelausa.com/sites/default/files/styles/large/public/2023-03/Principe%20Chocolate%208%20ct%20SS_0.png.webp?itok=kUSOkOjb",
            objective_date=date(2026, 4, 10),
            prediction=17,
            avg_weekly_sales=18,
            type="none",
            feature=False,
        )
    
    def is_first_start(self) -> bool:
        return False
    
    def register_user(self, user: User) -> dict:
        return {
            'status': True,
            'message': 'El correo a sido registrado'
        }

    def get_sales_history(self, barcode: str) -> list[dict]:
        return [{"date": "2026-03-19", "volume": 15}, {"date": "2026-03-20", "volume": 50}, {"date": "2026-03-21", "volume": 20}]
    
    def get_app_stats(self) -> ConfigStats:
        return ConfigStats(
            user_name="Roro Pirroro",
            email="elRoroPirroro@gmail.com",
            theme_mode=True,
            current_date=date(2026,1,29)
        )
        
    def get_server_status(self) -> bool:
        return True
    
    def sync(self) -> bool:
        return True