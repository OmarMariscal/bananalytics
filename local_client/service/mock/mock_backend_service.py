from shared.models.prediction import PredictionAlert
from shared.models.info_config import ConfigStats
from shared.models.user import User
from datetime import date
import time
import random
from datetime import datetime, timedelta

class MockBackendService:
    def get_alerts(self) -> list[PredictionAlert]:
        time.sleep(0.5)
        all_alerts = [PredictionAlert(
                product_name="Premium Cola",
                barcode="7501000123456",
                category="Bebidas",
                image_url="https://www.coca-cola.com/content/dam/onexp/co/es/brands/coca-cola/coca-cola-original/ccso_600ml_750x750.png",
                objective_date=date(2026, 4, 10),
                prediction = random.randint(0, 100),
                avg_weekly_sales=random.randint(0, 100),
                percentage_average_deviation=random.randint(-1000, 1000),
                margin_of_error= random.randint(0, 100),
                type="deficit",
                feature=True,
            ),
            PredictionAlert(
                product_name="Gansito",
                barcode="7501000152056",
                category="Postre",
                image_url="https://ayala-amaya-online.myshopify.com/cdn/shop/products/GANSITO50GR_dc4d79db-ad9c-443e-a4ea-70a2456d11fe_300x300.png?v=1595429786",
                objective_date=date(2026, 4, 10),
                prediction=random.randint(0, 10),
                avg_weekly_sales=random.randint(0, 10),
                percentage_average_deviation=random.randint(-1000, 1000),
                margin_of_error= random.randint(0, 100),
                type="superavit",
                feature=True,
            ),
            PredictionAlert(
                product_name="Príncipes",
                barcode="7741500152056",
                category="Galletas",
                image_url="https://marinelausa.com/sites/default/files/styles/large/public/2023-03/Principe%20Chocolate%208%20ct%20SS_0.png.webp?itok=kUSOkOjb",
                objective_date=date(2026, 4, 10),
                prediction=random.randint(0, 10),
                avg_weekly_sales=random.randint(0, 10),
                percentage_average_deviation=random.randint(-1000, 1000),
                margin_of_error= random.randint(0, 100),
                type="none",
                feature=False,
            ),             
            PredictionAlert(
                product_name="Doritos",
                barcode="7741500152056",
                category="Frituras",
                image_url="https://farmaciacalderon.com/cdn/shop/products/705419014010_1200x1200.png?v=1605548643",
                objective_date=date(2026, 4, 10),
                prediction=random.randint(0, 10),
                avg_weekly_sales=random.randint(0, 10),
                percentage_average_deviation=random.randint(-1000, 1000),
                margin_of_error= random.randint(0, 100),
                type="none",
                feature=False,
            ),
            PredictionAlert(
                product_name="Jumex Piña 1L",
                barcode="7501013121304",
                category="Bebida",
                image_url="https://jumex.com/wp-content/uploads/2025/05/flavorPina-format960.png",
                objective_date=date(2026, 4, 10),
                prediction=random.randint(0, 10),
                avg_weekly_sales=random.randint(0, 10),
                percentage_average_deviation=random.randint(-1000, 1000),
                margin_of_error=random.randint(0, 100),
                type="superavit",
                feature=True,
            ),
            PredictionAlert(
                product_name="Sabritas Original",
                barcode="7501011115626",
                category="Frituras",
                image_url="https://farmaciacalderon.com/cdn/shop/products/7501011165687_1200x1200.png?v=1605548666",
                objective_date=date(2026, 4, 10),
                prediction=random.randint(0, 10),
                avg_weekly_sales=random.randint(0, 10),
                percentage_average_deviation=random.randint(-1000, 1000),
                margin_of_error=random.randint(0, 100),
                type="deficit",
                feature=True,
            ),
            PredictionAlert(
                product_name="Leche Entera Lala 1L",
                barcode="7501020514106",
                category="Lácteos",
                image_url="https://freshify.com.mx/cdn/shop/files/pixelcut-export-2025-04-24T123157.062.webp?v=1745519534",
                objective_date=date(2026, 4, 10),
                prediction=random.randint(0, 10),
                avg_weekly_sales=random.randint(0, 10),
                percentage_average_deviation=random.randint(-1000, 1000),
                margin_of_error=random.randint(0, 100),
                type="none",
                feature=False,
            ),
            PredictionAlert(
                product_name="Chokis Original",
                barcode="7501000630622",
                category="Galletas",
                image_url="https://www.azucardulcerias.com/cdn/shop/files/6f10ba975498f8821ddd2eac464e14c0_1400x.png?v=1741900111",
                objective_date=date(2026, 4, 10),
                prediction=random.randint(0, 10),
                avg_weekly_sales=random.randint(0, 10),
                percentage_average_deviation=random.randint(-1000, 1000),
                margin_of_error=random.randint(0, 100),
                type="superavit",
                feature=True,
            ),
            PredictionAlert(
                product_name="Barritas Fresa",
                barcode="7501030432568",
                category="Postre",
                image_url="https://d5xnv1r45pn40.cloudfront.net/s3fs-public/productos/PRODUCTO_Barritas.png",
                objective_date=date(2026, 4, 10),
                prediction=random.randint(0, 10),
                avg_weekly_sales=random.randint(0, 10),
                percentage_average_deviation=random.randint(-1000, 1000),
                margin_of_error=random.randint(0, 100),
                type="deficit",
                feature=True,
            ),
            PredictionAlert(
                product_name="Takis Fuego",
                barcode="7501030454324",
                category="Frituras",
                image_url="https://www.barcel.com.mx/themes/custom/barceldos/images/files/takis_fuego.png",
                objective_date=date(2026, 4, 10),
                prediction=random.randint(0, 10),
                avg_weekly_sales=random.randint(0, 10),
                percentage_average_deviation=random.randint(-1000, 1000),
                margin_of_error=random.randint(0, 100),
                type="none",
                feature=False,
            ),
            PredictionAlert(
                product_name="Bimbo Blanco Grande",
                barcode="7501000110302",
                category="Panadería",
                image_url="https://farmaciacalderon.com/cdn/shop/products/7501000111206_1200x1200.png?v=1605546436",
                objective_date=date(2026, 4, 10),
                prediction=random.randint(0, 10),
                avg_weekly_sales=random.randint(0, 10),
                percentage_average_deviation=random.randint(-1000, 1000),
                margin_of_error=random.randint(0, 100),
                type="superavit",
                feature=True,
            ),
            PredictionAlert(
                product_name="Nito Bimbo",
                barcode="7501000111200",
                category="Postre",
                image_url="https://superlavioleta.com/cdn/shop/products/PAN_BIMBO_NITO_62GR.png?v=1752526538",
                objective_date=date(2026, 4, 10),
                prediction=random.randint(0, 10),
                avg_weekly_sales=random.randint(0, 10),
                percentage_average_deviation=random.randint(-1000, 1000),
                margin_of_error=random.randint(0, 100),
                type="deficit",
                feature=True,
            ),
            PredictionAlert(
                product_name="Yogurt Danone Fresa",
                barcode="7501032312015",
                category="Lácteos",
                image_url="https://www.danone.com.mx/wp-content/uploads/2023/05/7501032398514-WENDY-FRESA-MORA-220-OPTIMIZADO.png",
                objective_date=date(2026, 4, 10),
                prediction=random.randint(0, 10),
                avg_weekly_sales=random.randint(0, 10),
                percentage_average_deviation=random.randint(-1000, 1000),
                margin_of_error=random.randint(0, 100),
                type="none",
                feature=False,
            ),
            PredictionAlert(
                product_name="Agua Ciel 600ml",
                barcode="7501055300071",
                category="Bebida",
                image_url="https://www.qin.mx/img/catalogo/productos/producto-19-img-32.png",
                objective_date=date(2026, 4, 10),
                prediction=random.randint(0, 10),
                avg_weekly_sales=random.randint(0, 10),
                percentage_average_deviation=random.randint(-1000, 1000),
                margin_of_error=random.randint(0, 100),
                type="superavit",
                feature=True,
            ),
            PredictionAlert(
                product_name="Emperador Chocolate",
                barcode="7501000611232",
                category="Galletas",
                image_url="https://smartlabel.pepsico.info/028400344692-0005-en-US/images/42e84625-d40f-47da-b867-8e6d0a68b3bb.png",
                objective_date=date(2026, 4, 10),
                prediction=random.randint(0, 10),
                avg_weekly_sales=random.randint(0, 10),
                percentage_average_deviation=random.randint(-1000, 1000),
                margin_of_error=random.randint(0, 100),
                type="deficit",
                feature=True,
            ),
            PredictionAlert(
                product_name="Ruffles Queso",
                barcode="7501011115657",
                category="Frituras",
                image_url="https://farmaciacalderon.com/cdn/shop/products/7501011104099_grande.png?v=1640876038",
                objective_date=date(2026, 4, 10),
                prediction=random.randint(0, 10),
                avg_weekly_sales=random.randint(0, 10),
                percentage_average_deviation=random.randint(-1000, 1000),
                margin_of_error=random.randint(0, 100),
                type="none",
                feature=False,
            ),
            PredictionAlert(
                product_name="Pingüinos Marinela",
                barcode="7501000152063",
                category="Postre",
                image_url="https://farmaciacalderon.com/cdn/shop/products/7501000153800_77f73310-a915-4bb3-92b2-63025be1ff08_1200x1200.png?v=1625581089",
                objective_date=date(2026, 4, 10),
                prediction=random.randint(0, 10),
                avg_weekly_sales=random.randint(0, 10),
                percentage_average_deviation=random.randint(-1000, 1000),
                margin_of_error=random.randint(0, 100),
                type="superavit",
                feature=True,
            ),
            PredictionAlert(
                product_name="Peñafiel Limón 600ml",
                barcode="7501013410217",
                category="Bebida",
                image_url="https://cdn.alsuper.com/products/387656.png",
                objective_date=date(2026, 4, 10),
                prediction=random.randint(0, 10),
                avg_weekly_sales=random.randint(0, 10),
                percentage_average_deviation=random.randint(-1000, 1000),
                margin_of_error=random.randint(0, 100),
                type="deficit",
                feature=True,
            ),
            PredictionAlert(
                product_name="Zuko Jamaica",
                barcode="7501018501231",
                category="Bebida",
                image_url="https://www.zuko.com.mx/wp-content/uploads/2023/11/ZUKO_JAMAICA_GOOD-min.png",
                objective_date=date(2026, 4, 10),
                prediction=random.randint(0, 10),
                avg_weekly_sales=random.randint(0, 10),
                percentage_average_deviation=random.randint(-1000, 1000),
                margin_of_error=random.randint(0, 100),
                type="none",
                feature=False,
            ),
            PredictionAlert(
                product_name="Salmas Saníssimo",
                barcode="7501000142101",
                category="Galletas",
                image_url="https://sanissimo-com-mx-assets.s3.amazonaws.com/styles/interior_productos/s3/2022-01/Render_SalmasMaiz_144g_Saniss_Mex.png?VersionId=4uUOxGLeovtEM2zwSH_297XiGJzdaZBl&itok=bkyxtE48",
                objective_date=date(2026, 4, 10),
                prediction=random.randint(0, 10),
                avg_weekly_sales=random.randint(0, 10),
                percentage_average_deviation=random.randint(-1000, 1000),
                margin_of_error=random.randint(0, 100),
                type="superavit",
                feature=True,
            ),
            PredictionAlert(
                product_name="Chocoroles",
                barcode="7501030432575",
                category="Postre",
                image_url="https://marinelausa.com/sites/default/files/styles/large/public/2022-05/BBK17-016-Marinela_ChokoRoles_80g_0.png.webp?itok=l5C71EQh",
                objective_date=date(2026, 4, 10),
                prediction=random.randint(0, 10),
                avg_weekly_sales=random.randint(0, 10),
                percentage_average_deviation=random.randint(-1000, 1000),
                margin_of_error=random.randint(0, 100),
                type="deficit",
                feature=True,
            ),
            PredictionAlert(
                product_name="Café Nescafé 200g",
                barcode="7501058611234",
                category="Despensa",
                image_url="https://www.nescafe.com/es/sites/default/files/styles/pdp_banner_image/public/2026-03/natural%20%281%29.png.webp?itok=ZULGvlYB",
                objective_date=date(2026, 4, 10),
                prediction=random.randint(0, 10),
                avg_weekly_sales=random.randint(0, 10),
                percentage_average_deviation=random.randint(-1000, 1000),
                margin_of_error=random.randint(0, 100),
                type="none",
                feature=False,
            ),
            PredictionAlert(
                product_name="Aceite Capullo 900ml",
                barcode="7501006552011",
                category="Despensa",
                image_url="https://api.inolasa.com/images/Capullo-Plus-4,5-frente.png",
                objective_date=date(2026, 4, 10),
                prediction=random.randint(0, 10),
                avg_weekly_sales=random.randint(0, 10),
                percentage_average_deviation=random.randint(-1000, 1000),
                margin_of_error=random.randint(0, 100),
                type="superavit",
                feature=True,
            ),
            PredictionAlert(
                product_name="Mayonesa McCormick 390g",
                barcode="7501003301234",
                category="Despensa",
                image_url="https://www.almercadito.mx/cdn/shop/products/63_MAYONESA_390_grs_MCCORMICK.png?v=1640040185",
                objective_date=date(2026, 4, 10),
                prediction=random.randint(0, 10),
                avg_weekly_sales=random.randint(0, 10),
                percentage_average_deviation=random.randint(-1000, 1000),
                margin_of_error=random.randint(0, 100),
                type="deficit",
                feature=True,
            ),]
        
        tam = random.randint(1, len(all_alerts))
    
        # 3. 'random.sample' elige elementos ÚNICOS de la lista automáticamente
        list_return = random.sample(all_alerts, tam)
        
        # 4. Asignarles el tipo y feature aleatorio a los elegidos
        for alert in list_return:
            opcion = random.randint(1, 3)
            if opcion == 1:
                alert.type = "none"
                alert.feature = False
            elif opcion == 2:
                alert.type = "deficit"
                alert.feature = True
            else:
                alert.type = "superavit"
                alert.feature = True
                
        return list_return


    def get_dashboard_stats(self) -> dict:
        time.sleep(0.5)
        return {
            "total_scans_today": random.randint(0, 10000),
            "active_predictions": random.randint(0, 10000),
            "pending_syncs": random.randint(0, 10000),
            "is_online": True,
        }
        
    def get_product_detail(self, barcode: str) -> PredictionAlert:
        time.sleep(0.5)
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
        op: int = random.randint(0, 1) == 0
        return False #if op else True
    
    def register_user(self, user: User) -> dict:
        time.sleep(0.5)
        return {
            'status': True,
            'message': 'El correo a sido registrado'
        }

    def get_sales_history(self, barcode: str) -> list[dict]:
        time.sleep(0.5)
        """
        Genera un historial de ventas ficticio.
        cantidad_dias: Número de registros a generar.
        """
        # Simulamos un pequeño retraso de red (opcional)
        # import time
        # time.sleep(0.5)

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
        time.sleep(0.5)
        return ConfigStats(
            user_name="Roro Pirroro",
            email="elRoroPirroro@gmail.com",
            theme_mode=True,
            current_date=date(2026,1,29)
        )
        
    def get_server_status(self) -> bool:
        time.sleep(0.5)
        op: int = random.randint(0, 1) == 0
        return False if op else True

    def sync(self) -> bool:
        time.sleep(0.5)
        op: int = random.randint(0, 1) == 0
        return False if op else True