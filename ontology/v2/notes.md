Data,eH,PH,BP,S,BT,Nome,Categoria,Chamada?,Bonde?,Chuva?,🗺️,📝,🎨,Post IG,Rota,Ativ. Strava,Ativ. RWGPS,Horário,Partida,Chegada,# presentes,# novos,# strava,kJ anunc.,kJ med.,% Mov,Tempo Total,Tempo Mov,Potência Média,Quilojaules Ag. Total,litros gasolina ag total,Tempo Ag. Total,Tempo Ag. Mov,#midias,Descrito no Doc,Fotos Coletadas,Presenças 







## Columns

- date (date)
- uuid (int)
- Pedal Hidrográfico Tour numbering (int)
- Had public announcements? (bool)
- Had bike-lift before? (bool)
- Has rained? (bool)
- Who did the route? (list of Person)
- Who did the writing? (list of Person)
- Who did the art? (list of Person)
- Instagram post URL
- Planned Route URL (eg. RideWithGPS link)
- Actual Activity Route URL (eg. Strava link)
- Planned departure time (datetime)
- Actual departure time (datetime, either derived from actual activity or observed directly)
- Actual arrival time (datetime, derived from actual activity or observed directly)
- How many people? (int, either derived from Attendance or observed directly)
- How many new people? (int, either derived from Attendance or observed directly)
- How many strava activities? (int, either derived from Attendance or observed directly)
- Announced energy expenditure in quilojaules (float, derived from planned route)
- Actual energy expenditure in quilojaules (float, derived from actual activity)
- Fotos coletadas (int, derived from Photos)
- Presenças (list of Person)
- Novas Presenças (list of Person)