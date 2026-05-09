from shared.models.prediction import PredictionAlert
from shared.models.info_config import ConfigStats
from shared.models.user import User
from datetime import date
import time
import random
from datetime import datetime, timedelta

class MockBackendService:
    def get_alerts(self) -> list[PredictionAlert]:
        time.sleep(0)
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
        time.sleep(0)
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
            ]

    def get_dashboard_stats(self) -> dict:
        time.sleep(0)
        return {
            "total_scans_today": 1247,
            "active_predictions": 23,
            "pending_syncs": 8,
            "is_online": True,
        }
        
    def get_product_detail(self, barcode: str) -> PredictionAlert:
        time.sleep(0)
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
        time.sleep(0)
        return {
            'status': True,
            'message': 'El correo a sido registrado'
        }

    def get_sales_history(self, barcode: str) -> list[dict]:
        time.sleep(0)
        """
        Genera un historial de ventas ficticio.
        cantidad_dias: Número de registros a generar.
        """
        # Simulamos un pequeño retraso de red (opcional)
        # import time
        # time.sleep(0)

        historial = []
        hoy = datetime.now()
        cantidad_dias: int = random.randint(0, 100)

        for i in range(cantidad_dias):
            # Restamos i días a la fecha actual para ir hacia atrás en el tiempo
            fecha = hoy - timedelta(days=i)
            
            # Generamos un volumen aleatorio entre 5 y 100 (puedes ajustar el rango)
            volumen_random = random.randint(0, 100)
            
            nuevo_registro = {
                "date": fecha.strftime("%Y-%m-%d"),
                "volume": volumen_random
            }
            historial.append(nuevo_registro)

        # El bucle genera de hoy hacia atrás, así que volteamos la lista 
        # para que la gráfica la lea de más antiguo a más reciente.
        historial.reverse()
        
        return historial
    
    def get_app_stats(self) -> ConfigStats:
        time.sleep(0)
        return ConfigStats(
            user_name="Roro Pirroro",
            email="elRoroPirroro@gmail.com",
            theme_mode=True,
            current_date=date(2026,1,29)
        )
        
    def get_server_status(self) -> bool:
        time.sleep(0)
        return True

    def sync(self) -> bool:
        time.sleep(0)
        return True