def dpd_delivery_info(item_l, item_h, item_w, item_weight, item_volume, order, text_on_label):

    print(f"____________Sprawdzanie paczki DPD o wymiarach____________ {item_l}x{item_h}x{item_w} cm, wadze: {item_weight} kg, objętości: {item_volume} cm3")

    max_volume = 300
    max_weight = 31.5
    max_dimension = 150

    # wymagane, informacje o paczkach. Maksymalna liczba przesyłek dla przewoźników to: 10. Maksymalna liczba paczek wchodzących w skład jednej przesyłki (dotyczy tylko DPD i WE|DO) to: 10.

    if item_volume >= max_volume or item_weight >= max_weight or item_l >= max_dimension or item_h >= max_dimension or item_w >= max_dimension:
        order.errors(f"❌ 1599 Przekroczono maksymalną objętość paczki dla zamówienia {order.order_id}. Maksymalna objętość: {max_volume} cm3. OBECNA OBJĘTOŚĆ: {item_volume} cm3.")
        order.save(update_fields=["errors"])
        return None

    if item_volume < max_volume and item_weight <= max_weight and item_l < max_dimension and item_h < max_dimension and item_w < max_dimension:
        print(f"______________Paczka DPD mieści się w dopuszczalnych wymiarach i wadze. {item_l}x{item_h}x{item_w} cm, wadze: {item_weight} kg, objętości: {item_volume} cm3 ______________")
        packages = [
            {
                    "type":"PACKAGE",     # wymagane, typ przesyłki; dostępne wartości: PACKAGE (paczka), DOX (list), PALLET (przesyłka paletowa), OTHER (inna)
                    "length": {    # długość paczki
                        "value":item_l,
                        "unit":"CENTIMETER"
                    },
                    "width":{    # szerokość paczki
                        "value":item_w,
                        "unit":"CENTIMETER"
                    },
                    "height":{    # wysokość paczki
                        "value":item_h,
                        "unit":"CENTIMETER"
                    },
                    "weight":{    # waga paczki
                        "value":item_weight,
                        "unit":"KILOGRAMS"
                    },
                    "textOnLabel": text_on_label    # opis na etykiecie paczki
                
        }]
        

        print(f"*******************Zsumowano paczkę: Wymiary {item_l}x{item_h}x{item_w} cm, Waga: {item_weight} kg, Objętość: {item_volume} cm3 przy dopuszczalnych wymiarach: {max_l}x{max_h}x{max_w} cm ************************")
        return packages