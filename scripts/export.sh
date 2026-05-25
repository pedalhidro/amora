#!/usr/bin/env bash
#
# Gerado por coletor_apple_photos.py em 2026-05-25 16:13.
# Exporta as fotos de cada pedal do Apple Photos — uma chamada
# `osxphotos export` por foto. Rode você mesmo, no Terminal.app:
#     bash export.sh
# Sem 'set -e': o script segue mesmo se uma foto falhar.
#
set -u

# === PH 1 — 1 foto(s) ===
DEST='/Users/danlessa/pedais/2024-09-09 - PH 1 - Água Preta e Tiburtino'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid C9A03DE3-78B0-41FC-BD1A-AC4C114B6329 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2024-09-09 '-XMP-ph:RideName=Água Preta e Tiburtino' -XMP-ph:RideDate=2024-09-09 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 1 — Água Preta e Tiburtino' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 1' '-XMP-dc:Subject+=PH 1' '-XMP-ph:RideCodes+=eH 1' '-XMP-ph:RideCodes+=PH 1' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === Coruja e Verde — 10 foto(s) ===
DEST='/Users/danlessa/pedais/2024-09-16 - Coruja e Verde'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid B88C7F3F-C937-4C42-85B7-7977E08B4BF1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1E48C9CB-0ACA-456D-B85C-8AA7E2D39A33 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 54142F39-6786-44C5-94AB-B326E418D4F1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FB9D3DCD-79C4-429F-96B6-5090C4C81E72 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3DB6AE96-20C0-4ABA-BEE8-7B550ED0A18D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 304A774E-D40F-418D-91DB-ABED98ECCA86 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6FD0B7D8-78CD-4CEC-85B5-8B82553B7E89 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9E300EF8-91A5-48E7-ACFE-0F1CC4B45310 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2B7D0649-DC74-45F8-A92C-D740A0D54888 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FA8E3381-170D-4AF4-996C-7CEAC8A434BD --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2024-09-16 '-XMP-ph:RideName=Coruja e Verde' -XMP-ph:RideDate=2024-09-16 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=Coruja e Verde' '-XMP-dc:Subject+=Pedal Hidrográfico' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === Altos do Sumaré e Verde I+II — 15 foto(s) ===
DEST='/Users/danlessa/pedais/2024-09-23 - Altos do Sumaré e Verde I+II'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid B83252BA-427C-43D1-9E9D-575AD30C8C2F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D722F8E7-D448-4456-B567-F8707696A49F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2CBED24B-A593-4638-ADC9-95C8623C3BC7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6595B9DA-C401-44FB-A962-78EB491518CB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 79B2C42F-F06F-4D0F-976C-00023048EADC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DD1E53B5-0C65-4F8E-A872-2CE64618837F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 461F866F-88E3-4976-BDB3-9949C77F12E0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 01800B62-406C-450F-892F-09D0CAC51572 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 24A36957-A00D-4F2B-A48B-050ADC177494 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A9041A7C-EBD0-4AD3-B0AD-4A78D9EB9313 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B9016A59-3372-4ED7-8291-D0C01EEA219E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0E1B8FA3-CCB4-481A-91F6-B24A914C4199 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9093D476-0F42-4EBB-9161-7BFA8255D449 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BF274FC1-D7D3-4CEB-B13D-50E3D8330AEE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2B8DC857-25EA-4E11-882A-34A1E5A9D1ED --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2024-09-23 '-XMP-ph:RideName=Altos do Sumaré e Verde I+II' -XMP-ph:RideDate=2024-09-23 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=Altos do Sumaré e Verde I+II' '-XMP-dc:Subject+=Pedal Hidrográfico' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === Coruja, Bellini e Parque Lapa — 50 foto(s) ===
DEST='/Users/danlessa/pedais/2024-10-01 - Coruja, Bellini e Parque Lapa'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 9C58A9CC-796F-4FEE-A1E3-4E8BEEDB018C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 46D3AE4C-1B3F-4F49-8010-0D6ED486797C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2FFA1715-3A3F-40E8-9061-0B4BC32ACEC2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EF1E0182-A8C8-4399-81B4-1023F7B7B313 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C08EA59B-E829-4906-B07B-E670D7130A12 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EF992DA1-9222-4289-858D-DAF42C357AFC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3B63ADA7-30A9-4120-B74E-F13729AC0761 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 55D2EFB9-295D-468B-AA9C-25E6B32FBCE3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DBAE6439-8EA5-4863-B32D-91464B8A6E82 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D71C195D-13D7-417D-B00A-2BC28466292B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D73E127C-FC36-4C25-AAEA-B0EA1E9BFB20 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D3229B26-661B-4214-9C10-0143DDAEFE18 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 51BC11D3-1BD5-4FB1-ABEA-0CF9061F4EC4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7CDA14B5-2CEE-4DE5-9D9D-78FB105551B1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3E27A50B-F5EA-474C-A797-496CFF5B45EC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1E195491-CFE2-4DDD-B1D1-D299AB387902 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4D31BC91-C14B-4C11-850A-10CF609A7851 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9171AB50-0B94-4014-8BD4-78B05C23259C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 20934835-4FE3-4652-8317-D617F9244C50 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5B7D0E5F-35CC-4578-9896-23B8212E4EFB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 97A9BD7D-1E9D-4CB2-9486-9918EDA0BF14 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F38F3399-2CE5-466A-BD8B-737339C3D6A4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 29ED8086-0E7A-4EDF-AE62-9F68BDC6E362 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 71B3C745-A53F-4D46-8863-BF5AC185BE27 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D25F226A-6F02-4C50-9EAA-A5473619EA3C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AD7BBCE7-739E-4BF5-84B7-F5FE514291AD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D8FB6627-39A2-4E29-A79F-5F49CCF2CAD6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3ABD59E2-B5E5-4AC3-AD95-CFC0ADDF32D5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FD47FA85-9DAF-4B27-A4AC-922D19041632 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3A8B17D4-8CB0-4489-9269-2EEB0B866D5C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EA185D28-DF6A-4075-874A-E8BACD6D7091 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FF624C52-0E9F-4BB5-B11F-9760A12F08C3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DAD428A8-79D3-412A-A045-9D04A79585C4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 29FA6323-8911-4E04-AE7C-7B8BC8DDAF17 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D08AF907-B3A0-44CC-B087-668956BB1193 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 86024033-D0A7-41A2-817C-1302783DEF1F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CD18D21E-C052-48F5-B945-5CB08E4CB0C3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 61BF6E35-7B69-4582-B8FA-C1D301D50DB0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 30B249AD-6DAC-4A02-83E3-7FFFCD37DBFF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8D2BBDD9-69FF-4C61-AAB6-567B5047A1CC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6BAD1178-7B43-4C46-8BC2-099449004B62 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 14CD5157-043D-4CCD-BD85-EA04116C20CF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 56922337-8234-4F32-B7B5-CFDD1FCE19B2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 67D9E3E1-510D-4D41-AC02-D9C06A096284 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B34EB462-2F3E-4655-84DC-72F59894E058 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1927BF13-D5E5-40C8-8F8F-B14A4B6E6C54 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 26A4A730-5F8A-42CE-B412-89E2B0F34503 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6D056FCC-1801-440D-995E-F89D82379C7E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2795BCC3-E26C-4839-9CBE-D05B090F6EDB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 00346382-FF58-4CF2-ABF3-04BE88CFD959 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2024-10-01 '-XMP-ph:RideName=Coruja, Bellini e Parque Lapa' -XMP-ph:RideDate=2024-10-01 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=Coruja, Bellini e Parque Lapa' '-XMP-dc:Subject+=Pedal Hidrográfico' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === Santa Cecília e Saracura — 37 foto(s) ===
DEST='/Users/danlessa/pedais/2024-10-08 - Santa Cecília e Saracura'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 2DF6175F-1223-47DF-AF4E-5CFC9F2D68CC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E4E8A67E-C11D-4D40-BEAF-792157E0C20B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8AAFC4AB-670A-464E-81CA-8D766C9989DC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E70A4BDD-586C-427B-95F1-585609A6C38D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E5452C9B-D32C-45C2-92C3-432A18CE7E95 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 43D1775F-3915-4E76-9646-C8200A6D715A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 25B030B5-C5BF-437E-B9AB-CA3A2BABE9BA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0E757908-6A68-4E52-951E-A6B1722A15B8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BE0D7148-BA9C-4AE8-89B4-F0B58FC239A4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7F8AB4A9-0CC6-46EA-A407-3E0ED6BC221D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 260D391A-5D58-499C-8FF1-8ACA0AF3B21F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A52B2701-7496-4D83-AB70-BD342AE83077 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 971AC76F-BD1D-49BC-AF4E-5B273428E3E6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CBBC59D5-B319-46B0-B5FD-1CB7C571B419 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6B815857-106D-496D-B41C-496F74AD11C5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FA9203BF-2C5F-429C-951A-E03EBD6418C4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D10D71F4-AEFF-41A4-89B5-CB749AE8CE82 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6CA0E116-5752-4AC3-B0C4-BF11CDEA6DD1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B0B59124-EB1F-4455-AF52-A7397DC3A70E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 21BDC75B-AFDE-495F-AE39-FBBDC8DD801F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C401B091-40E8-4033-89FA-A1C7AFB1ADC5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F862158D-CD2C-4909-93FF-0DBF072E38A6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4C3D54AA-BF11-4FF9-8638-21A5775DA63F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2A58FE50-6CC5-4E04-AC01-9B06604215D1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1CAC76EE-50CC-4274-A3DD-D402D8BDEC70 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CE48B265-618A-427A-A752-547ACD492136 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3EA2B060-81F3-4A89-850B-93BF355ABFB0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 034E4A49-5C72-48B3-AC6C-BF9A9EC7EE4E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 542E9BD2-59DF-4148-8D37-583830BEB258 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D61979A5-5526-4501-B80D-1A745FDD527D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DD7B368B-8F50-4DBE-A399-728369E24E37 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DA901683-7559-49A1-8CBD-62E4C1267B81 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 386ACAB9-C705-4B03-9E6E-E90DE6D04150 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8DC105D3-3870-4EE2-9CAD-C0C82DD583BF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0EF94FF5-78EF-49CC-BB92-1A3572B3FA82 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7A9EA005-0201-4E6F-88B9-BE934FBC438F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B08A148C-A066-4627-AFA1-74052EFDB50C --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2024-10-08 '-XMP-ph:RideName=Santa Cecília e Saracura' -XMP-ph:RideDate=2024-10-08 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=Santa Cecília e Saracura' '-XMP-dc:Subject+=Pedal Hidrográfico' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === Crista de Perdizes, Altos do Água Preta, Tiburtino e Mercedes — 5 foto(s) ===
DEST='/Users/danlessa/pedais/2024-10-15 - Crista de Perdizes, Altos do Água Preta, Tiburtino e Mercedes'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 293E1675-D65F-4A30-B363-D32EE9160C6B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CE01281E-DECE-4076-9837-11D338AB80B1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F65CEF9E-2656-4E38-9F68-B9EEBC8AA732 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B3D79F4A-683A-4F29-822A-4B78B4BDD265 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 57D5A2E8-C2CA-4687-968D-C8B3D8B93BC1 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2024-10-15 '-XMP-ph:RideName=Crista de Perdizes, Altos do Água Preta, Tiburtino e Mercedes' -XMP-ph:RideDate=2024-10-15 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=Crista de Perdizes, Altos do Água Preta, Tiburtino e Mercedes' '-XMP-dc:Subject+=Pedal Hidrográfico' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === Verde, Anhanguera e Sapateiro — 56 foto(s) ===
DEST='/Users/danlessa/pedais/2024-10-22 - Verde, Anhanguera e Sapateiro'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 58451779-6C76-4616-8B97-FA50E19821A7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3B2CE1A6-C50D-46FC-BE89-0CB89159D11C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B6E14B95-F6FD-4EDE-9194-163463CC1298 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C58A6433-1167-4A52-9C42-748A3778E601 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AA01433E-B34B-4EEC-BB8D-D3F5BF2DFAE9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8C6458AD-BF84-4C67-833A-87A490183367 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FF3C64F9-6F4B-4B4F-90EC-DC18DB25FD90 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AE9F8635-0AD3-40B3-A115-E47930C79E67 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 92F79A28-BD9F-4446-9FD0-CF92D83ACFE0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 09F0AD06-F095-479C-ACD9-1FF843DF6B7E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 24D5E4A4-0476-4654-A7D4-DEC3CDA4BD89 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5A14D38B-4CA7-49E1-A40E-3E0492546143 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 909D2E82-2333-456A-A67D-BB264FBAA607 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F87E8974-3F20-43AE-A9EC-4950485BBFE1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9A4485C9-FA1E-4FB9-A778-B7E35A3D68D6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AA6B420A-0D40-409D-8481-5467B814086D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 22C2F90A-6F6E-4FB1-9321-BA5A69813118 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8607CE2A-1A3E-4CF5-9053-B422690F6638 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 02B24CA1-A52B-4778-8659-D1E7229CF8CD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 05828982-D3BA-422E-BEDA-71A620A5F496 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6BA194C1-4FDD-44BA-A513-5D2C72F41AAB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4756288E-9453-450B-B967-88A1323DDB79 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A6B2F5C1-2EF3-48B9-A0C4-98A7E1A959A2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 15219970-8ACD-444F-A306-12DA5BD62167 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DE621151-9FB8-4370-B058-75CF03A86375 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0D2FE06F-698A-4857-9C59-20424336CB77 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9259E419-11B5-413F-9E7C-168DB9EA83DC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F0F1B00F-3947-4B54-B1AF-55E326795C40 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E20B38E8-49B3-4E02-9310-F9248FAB8759 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 124DDD14-E968-4F6E-A21B-8CF29554F1F1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 782C9BDA-FF44-4D56-8FA7-BCD5DCFF6092 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0CA9DE9A-4D2A-454C-A923-4702AA2998E0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 91C65E3C-D885-4E55-9D60-8DFE70BECD77 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 18AD0214-480F-4422-A2AB-9693478038D6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B0672C15-29B7-4982-B005-29E9C8E40D31 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8F490611-54C9-46A7-89A0-F4921CEFD3DC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6228A51E-ADE1-4647-A705-B60D89F7CD12 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 97BB12F7-841C-451A-9512-C6DE62B91511 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 98BCF7C4-3F43-4FB3-BDCA-5F93A42EC386 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B7763D2B-C9EF-431C-800F-EAB52BE54215 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 69F5ADF2-59A4-496A-B561-57EE3BEBEABE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E2FEE18B-E6DC-4199-AACD-AD4E070BCAFD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ADDEA2FA-6FDC-4460-BADA-33A18BB4C2F6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DA82E2F5-1622-4AAF-88E8-C81B11CECDAC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 67FF1BBC-6277-40EF-928F-74CB66F2EF8F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CF2D35CA-D502-4D32-9316-F80D965AA967 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6A7065B5-F61D-409E-8C93-2FBA6436E85D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A3890AB5-B310-4A9C-ACA4-FA110C863431 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F07A91E9-A61C-48EC-B4B3-857F30CA9073 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AA9BE31D-1F69-40C6-9F7A-77EF650FF94C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 91B919B7-E140-4865-9F66-4CF734F7A680 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1432A675-7C62-4B69-83D9-FEB1A7433F69 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 77E608A4-BF9B-414F-B1A6-666C32742AD7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6B9C2534-12B3-459E-9AAA-1CBD21E73BF6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1C0A2E55-3720-4AF1-943C-5F992F8296CF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5173BF9A-DE00-4332-9316-3BA2077F578A --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2024-10-22 '-XMP-ph:RideName=Verde, Anhanguera e Sapateiro' -XMP-ph:RideDate=2024-10-22 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=Verde, Anhanguera e Sapateiro' '-XMP-dc:Subject+=Pedal Hidrográfico' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === Itororó, Lavapés/Glicério e Aclimação/Cambuci — 21 foto(s) ===
DEST='/Users/danlessa/pedais/2024-10-24 - Itororó, Lavapés-Glicério e Aclimação-Cambuci'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 457C6728-3E6C-48E4-AB0B-2C05350B76FD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FF14BFE4-C0AD-4539-98EB-22BA4D2027B6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 30A8D21D-4F1D-438C-934D-63CE1D910B10 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5D1A6D01-175D-40EE-8B7D-CFE79AC1F122 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AA6FC7CA-62E8-4FCF-9D83-ABC0E31055BB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E529CE42-D09B-4443-9046-DAEBA8BD0EAC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3E6CD1AC-31A4-4659-89F1-B8EC319D2D81 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 28EC895C-0015-4FAA-A1E8-E46C12026C70 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DD343FCF-0EA6-4B8C-B9F9-BA81A7A86238 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4EBA2790-561B-4CC5-A087-4F283348946C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B23CDE7F-5DAA-4C50-A852-C0F6C872664A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D9778F28-1B48-4F32-BCDD-FD3A816D545A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AEC45897-28D2-4E95-BB7D-230164E61553 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9D195605-72EB-46A5-815E-E4215CC81282 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F54CB11C-D3B9-4394-8211-6405039C23C4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AD5E9616-4685-41FF-ABC8-6DDB3540E1E2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F8F33D4F-416C-408F-88FD-180FFD622459 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CA9EA1C4-7311-4DAD-A9CA-93F9AE2CC857 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DEDB81EA-C4BC-4427-A1FF-A2E92E497159 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 802BCD06-C8F0-4D99-AA48-88F5FCFFC894 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 865AE046-2C09-4B20-916F-41FBA5A8B769 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2024-10-24 '-XMP-ph:RideName=Itororó, Lavapés/Glicério e Aclimação/Cambuci' -XMP-ph:RideDate=2024-10-24 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=Itororó, Lavapés/Glicério e Aclimação/Cambuci' '-XMP-dc:Subject+=Pedal Hidrográfico' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === Sertões de Pirituba — 77 foto(s) ===
DEST='/Users/danlessa/pedais/2024-10-29 - Sertões de Pirituba'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 8B87184E-EFB9-471A-9B82-6363AFF42DBB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 54C80F69-8D5A-4E23-8DE3-C744BBE52F71 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A2438F43-199A-489D-9EBD-13724D3ECE1A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ADBB8C80-F3BA-4F3C-86C3-8BC15434ABA8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2763C9CC-2ED5-40A5-9146-8C95211AF9C1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 38F4C0B1-F841-4DEC-9417-CC5C767ACF24 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 549CF4EE-CCAF-41DB-94B9-C06D0CF1441A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 54EFF810-FF58-4E54-A658-5AAA467E9B9D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DDC79507-D7CB-45BD-AB58-C25C3AACA3B4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 99636C2C-B588-4459-A9EB-1E73A1294281 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5318E460-C4B9-4304-A4C4-3926D77B9F4C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EDFE055B-02A0-4BA5-A2BB-D1BE4E5CFBB7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2AE06E68-B784-42B2-AF06-DCFB510E080C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3B7504D5-FE39-4363-A898-D45C254D2F33 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 32C871BA-4F65-4335-A07A-82CCB3A5E5EB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B3F7589A-C961-4B90-864E-E4106254ABA6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0D285EC7-968A-4B08-8574-5AFCB7972098 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9166DFF5-AAAA-4BE3-A915-ECB6B35930C8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8C596DD8-08D0-4F43-8343-4261C303B9A6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 61D61F16-82FD-475F-97F7-4D8B60F8B3A2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 19000114-0DD8-4489-B406-0A7D6CC038E9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C52B5F6B-05D3-44A3-90F4-5200216F7342 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0E5F2383-0466-4E62-848E-A67C988C7CA4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CD9F40ED-087B-45F8-A4CD-46D7296153AD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1FB6EECD-22CF-41C5-AB17-DD6747394931 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E32164DA-FF0C-4687-B43F-CD890534A458 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7043ED7D-4C09-4E34-9142-E1804997CC56 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9A187F14-6D29-4BD4-AD5A-AAC8CFF85CB8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6CA901B3-F6C1-4F8E-93D7-D797B57B1109 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B5B95DE1-E2D9-460E-A26E-84C18668B3E6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 37A964BD-0FB7-4E25-A4E0-7B1F0B42E536 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8FD2906D-7F59-4D5A-A720-0900749C75F5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 64877778-EFBC-48B1-AA07-573975403F9A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EF4D5108-079D-4E04-9155-84E3352EC507 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A1C3DCCC-48A5-4197-88E3-9EC708C46F62 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 24309DE4-CEE6-4A18-9369-FA1E7385676D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EF02E9F4-840C-41FB-BBD9-6EB40E59D410 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3F27C02C-9D49-4842-97DA-8AD39BBDE4B9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D1DE00D5-7F78-4E63-9A1A-E6081F1E0430 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 12BEF37E-6599-4E97-A0B7-EE31C20C7811 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 73E9C264-7E64-40BC-AFA9-00E9F62630A8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D9FFD65C-1DE1-439D-90BB-B8DACC91B7AE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6A909B34-C8A2-414A-9CDA-1E8E2AFB8FB7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BA59794A-A37A-4F7F-9563-8555E065A88E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 48464BF1-D0DE-4DB1-9F71-A94F74F2A41B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 014AE662-56D8-4883-9571-C7E97EE214B2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F6C07E0D-E32E-443A-A04E-80BF233C6E0D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A73570D8-DD5C-4AAD-88A4-976190619C85 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CC4F0DA4-4C6C-4DDD-BCDB-5003DC3A1E30 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F06B0090-164A-47D0-868D-A313B1A78880 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0086FF7C-1E52-4424-940B-D9A48176556A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E5623580-3E12-4AF8-8AA8-F03070F72FF9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ED3D5949-B002-4C21-8E86-EBCA4C978CB4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5243A075-BF80-4CFF-996C-8208FC3E8613 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F9DA0620-6A2D-49AC-85EE-6C2824250869 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3495B55E-DB8F-4EF2-A5D7-1BED1ABB929B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 34E74FE9-BA1B-4451-8038-3CBB155A051B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 503785AC-B507-405A-9DBE-FD5512A807C0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E06C9A46-2EFF-4BAD-BDAC-E0C42008F48A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 57ACD9E1-FAEE-4A3D-80D7-04F1CE99FDA2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F12FF356-2CD1-4E87-9A4E-3734DCD25547 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AC3792FA-CDDF-4841-9517-9787143CD0AA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8875BB7A-BACF-430D-8E7A-3A31FC26B13E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B2443B76-622A-4CC3-BDDF-C7BF9061B31F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 04FD7541-C2AD-4988-892B-042B204DBE94 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 66D1024E-4923-494F-9EED-BE59CC0504F6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F2B62D99-5231-413A-A512-794007D73C3A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 821B18EE-48B1-48E9-98EC-285EAACA7868 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B1D3FFDF-48B8-4436-A69C-AEC9AC2B10F9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BC430124-6548-4AD6-9BC5-84DC172CDF25 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 92434BD9-DA60-4565-B28F-D7CFF5D4A044 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1A2CFA32-8965-436D-8011-FFBCFAF89F33 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DA54BDFF-F33F-4A51-BF75-6D0A85CCD2E5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4D223D17-BF28-4CD1-826F-493CBC8CABAD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1A08B200-2450-4A9E-832B-1C4F610E34D6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5A360D59-E4D1-4228-8601-CDB8B777A8C3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AF33E0DF-D097-4C3A-97BD-E8FEE242F361 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2024-10-29 '-XMP-ph:RideName=Sertões de Pirituba' -XMP-ph:RideDate=2024-10-29 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=Sertões de Pirituba' '-XMP-dc:Subject+=Pedal Hidrográfico' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === BT 1 — 2 foto(s) ===
DEST='/Users/danlessa/pedais/2024-11-02 - BT 1 - ABC'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 86F894AA-B592-4A21-9693-3465CEF16A4F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1CBCE20B-334E-460A-AA8E-13F0A4CC596E --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2024-11-02 -XMP-ph:RideName=ABC -XMP-ph:RideDate=2024-11-02 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=BT 1 — ABC' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=BT 1' '-XMP-dc:Subject+=BT 1' '-XMP-ph:RideCodes+=BT 1' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === Contornar Pacaembu e Sumaré — 51 foto(s) ===
DEST='/Users/danlessa/pedais/2024-11-05 - Contornar Pacaembu e Sumaré'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid A976AF85-5F91-4D0C-8FD8-377CFADA1E3C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0ACDF3BE-0EED-4C93-B0D4-CC2F40E940EC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ED453EB6-80FB-4A17-A9EB-94826A4B1831 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0C7445FB-4CEB-450D-8040-BAC2457A0505 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4BB0143D-9288-4812-8D9E-1B3A43CB824B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 209434D4-4E03-4F42-9BAB-1E5816B0BC7B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 180D0D0F-096A-4FCE-ADB4-E6432276E70A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 64CBC5C0-A18D-4239-B07A-51C78092BE92 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0006B5E2-9F6F-484C-931A-5EBB7F0906C4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F6569F8C-05F5-408E-A55C-57C261D4EC28 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F857598E-4044-4767-B841-0F9E5F8CC147 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6383C9F3-E02C-46FD-90F9-0AF4C144AAE3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6C7F73B7-9750-4A4F-9448-76E8FB37DA24 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 93CF3B41-E301-49B5-B640-40A93E70D224 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7B728331-9F94-49F1-802A-4FE4E4456C0C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BEDD3A1F-1F75-4A73-AE39-B4AD2A5C90B0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6513FAE4-7411-439B-A59E-735A5B161A62 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8E6361FF-BCB6-4CAA-88B6-CE7D0C3C9100 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 737ED236-5286-4626-ABBA-8D20A424CBBE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 37D4C930-407D-4262-A87F-80B7BC52B485 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 668D46E5-98C5-4C6D-891A-32174889A05C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 418D8D4C-2BA9-49D3-9ADC-769C8C1F2A51 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7E28AAB0-46A9-4B00-9F7E-34E20C2054F3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 513F287F-6A37-40F1-9653-A5422F858AA9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FDE9C286-5149-46E0-B6E6-BE39D1415A72 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 78AFB5FC-90D4-4A94-833F-5510BD676EC4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8F9F09C4-5B80-40C5-B1B8-D0B29E7E300E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 522A476F-B911-450A-AD41-80A8C96CC66C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 925F39FE-6AF7-46D6-87A7-3EDA00D47D7C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 37B7D0D3-0603-4504-B7FF-ADFA1C0483B6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 39E4E89F-1B6B-48E7-B475-FF11B5E5A604 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4F82E5ED-BC80-4E44-8398-D41FD184288D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 01DF84F4-2514-4CC3-8F10-29D1C29CC9E1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 520D7080-C939-4CC1-8022-1CD24FCACFCF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B971141A-56A2-4F43-B037-E779BB3D4B47 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 34599CF4-8995-4454-A8CB-8554412742BD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 678B002E-517F-4DBC-A43A-E84C48B330CE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D92822CF-515E-4D50-A569-01C75F4A0459 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3E0AB319-AA38-46C0-A841-F80A9C7ED528 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1B18DA2F-623B-4BA4-B923-35AA28296003 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CD9FC453-961A-404A-8A01-7B51D1667016 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E82D618F-D837-4B09-814D-09DD6B8FE1A4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4ABCDF1C-E5B8-454C-B409-CEB54F911CE1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DD28A3FF-9112-4101-B9CC-C154C9E6EE01 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BC90ABBC-421F-43F5-83A8-A26D52B1426C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 72B1D71D-B022-4E0B-8558-A65A94C0B9AB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 14F59DEC-EE6F-46EF-90F7-01D958BDCDA6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1F38272E-A833-43DE-ABBD-159B9105375D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A9159460-F50D-41AB-AE4D-9E74BFCFC3BE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 35D5ACA8-50F4-4B96-B1A9-F477DF400F88 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A59B3E44-F165-4B27-AD47-19C482422758 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2024-11-05 '-XMP-ph:RideName=Contornar Pacaembu e Sumaré' -XMP-ph:RideDate=2024-11-05 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=Contornar Pacaembu e Sumaré' '-XMP-dc:Subject+=Pedal Hidrográfico' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === Mirantes do Tietê com Pico do Urubu — 2 foto(s) ===
DEST='/Users/danlessa/pedais/2024-11-09 - Mirantes do Tietê com Pico do Urubu'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 2558BEAF-59D1-4667-966D-D070223717E3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2C02B71D-5364-4602-9EF1-47762BD6BD50 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2024-11-09 '-XMP-ph:RideName=Mirantes do Tietê com Pico do Urubu' -XMP-ph:RideDate=2024-11-09 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=Mirantes do Tietê com Pico do Urubu' '-XMP-dc:Subject+=Pedal Hidrográfico' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === Margens Ocidentais do Baixo Ipiranga — 81 foto(s) ===
DEST='/Users/danlessa/pedais/2024-11-12 - Margens Ocidentais do Baixo Ipiranga'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid A7BC2449-5892-4915-8C6F-51F2FF95674E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 516BC1AF-7AB5-4AA4-9364-F248A1A3F853 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3B12F0F8-4D41-4E13-9CA6-739E44B2C94E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 06FEDC95-BD47-465B-93BA-E05C0605BB88 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8567873A-DB34-4BB1-9224-672A1DD159CC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D2C01D4C-6B3A-4B9F-AB12-6649862DB331 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5A3995A6-5ED7-4053-88DB-40FDD9A72556 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EF439413-6E09-4940-9548-EDEF51B49D5C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 07387788-3F98-49F3-AABA-F809D4D404BE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2B1FF56D-55EA-4303-9EF6-41DA07015775 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9F26E2D1-8285-40EB-9762-BCE80FACB0EB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3173DFED-7710-49C2-A211-D72F3E9B63D0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7419B7B3-007D-409C-8F42-2F73B126370B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7C0295D9-FA1B-48AE-B534-8446CA05F09D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9D2A95F3-2EA6-417E-9BB9-0418C59213F5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 290F201E-8A4B-4F06-9814-66AC69E8921E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2886C375-0586-403F-976A-AAFD86E33293 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3C14B70F-8486-491A-83E9-4BD94BB16252 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5F8AF844-1D8D-4C72-A69F-CE977FC41C75 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8110A45E-A4B5-416F-AE41-049CFC0B43A5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FF13AF3D-B62C-48F3-8772-C28FA40DEDDF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C1541230-EB88-40DD-9D63-B53B332C0DE4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6D7D241A-6D4B-4420-8ED8-E0E8B2A49573 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C02BDACF-BEEF-4623-89CC-4A5534C56C0D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BD5F1F8E-A52A-468B-8C1F-6B2666D30A0F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 33B6A8AB-8414-4BF4-9A50-9D583057D0B0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 63DA1726-6492-4753-9538-B242A12B690D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C6663FDF-BD24-4D92-AFBA-FA09708946D6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1F8E078F-6EC0-4D37-A2FB-7594D2471986 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0B8282E7-0C08-40F5-A991-B98B5245F3A4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7FAD4540-D1FA-4EE2-A6F1-A29BB8A80CFA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0446CCFD-7495-4401-BFD9-3C7B12BA5DE4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 729F282B-4864-41D3-BBBC-80522BC11247 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0D64A554-0966-4B5D-B421-00CA53DEAE58 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8565A3EC-582B-408B-B483-8365D4C7FB8F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7E67602A-287A-4CD8-9CED-5F2674CE9C3E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F5611FAB-8367-4585-B2EE-595E4AC995CF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3AC2FC8C-2759-455A-B473-DB3F81F65701 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 31341F19-C883-43E3-8CC2-0F2C7B175944 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 457A1D32-EC7F-4164-B7C3-C1514D3C2C49 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 13E628C3-F864-4E13-AC35-450BE0D4B948 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7E96A036-B7C3-4D28-9E51-E18AFF7EBF81 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6962BE11-DE92-49D6-AEF1-D446D8F8B264 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 47886B6E-0C9C-4892-9486-4ABD4DD2FF69 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F5F2650B-DF81-42E6-9509-B27CB4EFECB8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 64AAC902-E42B-4728-8BE7-F931D535C598 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7A0C6F5E-E53C-40B7-8E6C-56F2A1EAF566 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4FC20871-7053-4BEA-92E1-D432569CBBB4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DECFEBCD-D448-45C7-B5D0-2879F3EF1B22 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 06FA77DC-6BEB-4966-A089-C1C656DB13AF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9AA0DA45-FBF7-4EDD-9FC7-CCE83A500F51 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 35D2F9E3-BF15-4E77-95CB-2D4AFB0541A3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C9859C0E-2B31-4B38-91D6-22CCC2366338 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ED6B3DD0-D860-4E83-8933-F42E868D1FBD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A2C61DBE-DDB0-411C-96D8-E8A3629056AE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 58182438-A2FA-482A-9E88-4F103958CF89 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 545E5FEE-1375-4ED5-A341-BA2C1ED67D0E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A8EB1E7A-762A-4B45-9EEF-9852129F6E50 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 96119755-AAF9-4D9D-BC16-79A70207775E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 00724604-4A09-439C-A556-A19796B708D5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 37C09F25-BFF8-46B6-84DD-31EB33244919 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A8766E94-B4AB-451D-B5A2-1DD936C59CA5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 05A43F4E-FA5B-4F2C-93BD-6AD6C426C30A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6B0EF813-69DB-40CA-B58C-0DBF17930963 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C75E31FC-90E6-49A1-A4DB-51D742301725 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FD69D83E-4E41-4345-8A42-497D4C706DF4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F0EDCBB0-23A6-4566-AB3D-FBB1D54B107D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E851961F-5C7E-44E1-9E30-B17C7A2ECB66 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 137EB7EC-9A76-4205-ADCE-B71CA34B8802 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3E4DD534-3B82-41F9-BF64-45A201CDB36D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9999EB95-6849-4C7C-B00E-F7A5062A022D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C57EFE10-EB73-428F-ADD5-7950E5A73CFD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BD18FD43-88B1-4471-B5CB-F1E974BEDAEF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 72C25EE8-CE49-417A-97F1-CF232832EBFF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 306116E6-8EC3-459A-B4EE-405384CA48BD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 39BAC3B4-A6B1-4A66-A1AA-9CFBB0A334D5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0375CD43-9774-4F1D-823B-8817DAA1FD6D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E087EE4F-EE9F-43C3-9C95-78D84F8C9B30 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3C1EEE3F-B6D1-4F79-A348-42DC90CC40E1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8E26EC8B-639C-450E-A262-002B99E11C2C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 47C9F869-02E4-4147-97FA-28CFD615C251 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2024-11-12 '-XMP-ph:RideName=Margens Ocidentais do Baixo Ipiranga' -XMP-ph:RideDate=2024-11-12 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=Margens Ocidentais do Baixo Ipiranga' '-XMP-dc:Subject+=Pedal Hidrográfico' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === Margens Destras do Baixo Jaguaré — 9 foto(s) ===
DEST='/Users/danlessa/pedais/2024-11-19 - Margens Destras do Baixo Jaguaré'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid BCA20BAF-E1F0-4ADC-9FF4-4C33659639DC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8FAE10AA-F211-465B-AFA4-021C9F945F66 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 24C31663-99DB-4D2C-B029-627463DC46E0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2BB5082D-7188-4E75-A640-97F71670251C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A44F9069-71FE-4CED-896C-5DADEF0AD4A4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6EDE9E73-EB1B-4836-8901-22A145A96A05 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2FF6E92C-ECD4-41A0-B5E5-2FB1FCED847D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 62C99A5C-8D46-4E24-88F0-A6B2795EC284 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 43E8F037-9F5D-482F-BE8F-E422D496D5BD --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2024-11-19 '-XMP-ph:RideName=Margens Destras do Baixo Jaguaré' -XMP-ph:RideDate=2024-11-19 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=Margens Destras do Baixo Jaguaré' '-XMP-dc:Subject+=Pedal Hidrográfico' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === S 1 — 5 foto(s) ===
DEST='/Users/danlessa/pedais/2024-11-22 - S 1 - Crista de Osasco'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 619097FE-D560-4BC8-A75A-921ADE9B9153 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4739D5B0-9E2F-4A4F-82CF-1B529C771017 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 64B89E99-A66B-471B-B6DE-D6F6A7DE56A2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A334CA7A-466E-4906-B412-EAC59A556E9A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5FF105B4-C1A2-4D73-A726-64AA2D8F1636 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2024-11-22 '-XMP-ph:RideName=Crista de Osasco' -XMP-ph:RideDate=2024-11-22 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=S 1 — Crista de Osasco' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=S 1' '-XMP-dc:Subject+=S 1' '-XMP-ph:RideCodes+=S 1' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 16 — 2 foto(s) ===
DEST='/Users/danlessa/pedais/2024-11-26 - PH 16 - Água Preta e Tiburtino'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid BD18597B-995A-4EFC-9F20-51C4E8EE8977 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 37B2F51A-92A6-41FD-89C3-5BA5B77091E2 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2024-11-26 '-XMP-ph:RideName=Água Preta e Tiburtino' -XMP-ph:RideDate=2024-11-26 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 16 — Água Preta e Tiburtino' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 16' '-XMP-dc:Subject+=PH 16' '-XMP-ph:RideCodes+=PH 16' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 18 — 47 foto(s) ===
DEST='/Users/danlessa/pedais/2024-12-03 - PH 18 - Contornar Iquirim e um pouco do Pirajuçara'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 1F6A7E46-BDD8-4650-9E78-16C5EAE99517 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7CD72D92-352B-45C9-8D57-A6AA45BDF20D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BE1FDB5E-0230-4713-9F91-85856968E5F6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F17E8A05-8ADB-4BDE-BF9A-F1BA10836438 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8503CC6D-1BA6-4638-AA9E-95334CBFA5EA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 04F87641-D5D4-42BD-906B-1DB79E1B0498 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 82C9F266-698D-4CE7-A623-FE424CD20935 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 95B3937C-DBA1-4E92-A9F8-6BA2F39447C3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0F62804B-F25C-459E-B7FB-F6E57C2C335D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4372ED5A-681F-4288-A2C7-E42661702996 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C88C3525-6E75-45B2-A506-58D0A3BD8DD6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 31435D78-311A-49A4-9B4C-03A7DFEE16F2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5CB32422-FCC5-461F-8BD1-6C5779668B25 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D7044E8C-8F8A-4405-8A2F-5590ECB6E8E5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 39818A7A-EAAE-4840-B240-E8FAD2C9B3BE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F964336B-F9E3-4930-9B5B-E5B4A3299A0E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3BC52F84-DCDA-4C55-8EDB-9A19ECFC5C5A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 54741202-25DF-4180-9F8C-B0A08A3C9668 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DD9BE451-E961-4CC2-ACF0-4286A05578C7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C735A3AA-D25D-475F-A726-2C21FA7C730B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 966A6780-8D1F-49A7-83AF-7B51EEEC114E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 404218A5-5FC6-45C4-9B26-990E1267522A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0BAFAFB4-AA1C-40F1-898F-EB21F2FBB06D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5CBA2C06-32D6-4C9B-9929-7530925A2ECC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9AD59BF1-A829-4F11-B232-FB248CAFE105 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3F5CF185-1ED3-4C89-991C-7B2E2E0E62EF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5E88D9EC-8889-4E4E-955E-827212049E00 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D8AB307C-577C-4D79-8346-DDAD59A6BF2F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A8981AB7-EB71-4439-8BF4-76D068E5F2B6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 45C6EBC3-A82C-478C-92A7-282353F45D24 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1E7ED264-E47D-490D-9301-A426F85E0D74 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E2DCD224-A4F2-4D1F-BC7A-A9A760D53833 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 88DDA332-582E-45E1-84F6-2719D46ED89F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 079DBB72-BF9B-499C-94EA-AB8F44D68B0C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1FDBD4AA-59A4-42C8-BC49-21F14B9B58D7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0A5D0506-874C-4CDC-8A43-392DFBD08110 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 78D57A06-9805-4214-B809-F75C2380F90F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0070B590-9BFB-4F35-9167-5E895B7164A2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A88FA81F-4CD7-4B1C-8DE6-AA6EEC7CFC5C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FD822E05-1BD1-460B-835E-03A450EB6A38 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 56CBAA4C-903E-420F-B9B6-CC57780C9BDC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BC3F92B5-EEB1-44DB-A4E4-21B4908874F0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9D2C22B5-05B9-41C9-A374-4CB2012B5506 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5BF9A7F0-BFDA-4FD9-A6A5-D7D7BFD56C79 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 666DC9AB-3B2E-45F6-91EA-B96E5F2C822C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2F5CC810-99C8-4EDC-94DA-0C763405BC35 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 35AC26CC-F891-453C-94E1-4BDBFC3CB291 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2024-12-03 '-XMP-ph:RideName=Contornar Iquirim e um pouco do Pirajuçara' -XMP-ph:RideDate=2024-12-03 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 18 — Contornar Iquirim e um pouco do Pirajuçara' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 18' '-XMP-dc:Subject+=PH 18' '-XMP-ph:RideCodes+=PH 18' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 19 — 61 foto(s) ===
DEST='/Users/danlessa/pedais/2024-12-10 - PH 19 - Nascentes da Brasilândia'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid B26DEF8F-F76E-4C72-B3B6-39E90B01107B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3091A2C2-F915-4857-8376-2306A34671DB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 970711F3-F52B-4E03-85F1-057AD0CBD284 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AD1AAFFF-3C14-4318-99B7-6E8F57FFAAE6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2A986DD6-BC23-47F7-A693-D62750ACF9A3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7C1CC570-17AB-495F-83E5-2E3CB46B998B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A9115485-558F-48DC-B643-58BBDADB69A8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 83F81FD6-C03F-4B55-9270-C7739792913B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7C3F3748-81F8-448C-85FC-F1A8E64D40B5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0DDB3495-9555-4832-844E-9A138DA0ADC3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F36D5062-2B11-4505-9135-1A7053A5C404 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A4024924-B5FD-4B8C-B306-E133EF39A2FA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 57EE9B47-972A-4ED7-B791-F1665D397D39 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A4640814-7C1F-441D-8571-8759A9857EBC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 29870A40-6C64-434C-9555-0EBB40D4799C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 12B977B7-8875-4AC9-8433-BA499CF3A96B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 972EA078-3105-4AD2-B70C-6935DF1EE25F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6DFD6061-4581-42D2-9FDF-73DF2F6FE7B4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7639D213-297B-43C2-B149-7A6EED82C434 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AAD100EE-FC51-46FC-9939-D58F3D0C2659 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5DBF0B14-978F-4317-91CB-E6E907BFA6FB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 03583C3F-A2AD-4275-81C7-EBB3CCF8062A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8B4B7B90-B479-4268-89FC-C716F84A3F3F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DEBDF3AC-E6F9-4015-871C-C640EFE9CDC6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7C3EFD92-6B50-44EF-9851-871F70D5F428 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C587FE80-F0F8-479E-A602-C9F9B110D9EB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1FEEB479-CECB-44AB-A11E-2D17EE150A40 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4E7F3135-8EAF-4F7F-BA22-A00528E69EA3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 58C66CBC-7F3E-42CA-AEED-F941C4EAB05A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A28D4B88-7CE0-4737-BBCD-D3BCE4220C04 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3D884DF9-AD86-434E-BBF5-7E488943A336 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 979BBA98-8BE1-47AA-B952-9D2D5768EA1C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EA371229-6268-4F90-B5F3-84A1D82B0064 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2D4A0310-68A1-448E-A333-4890E14E1ACD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C4DCE248-6C7E-486E-ADA9-B38FFD3D62DD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F65916FC-1107-4034-BB3A-F6337DA46B40 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 09A951BA-A49C-4535-BCB1-3E2E76BE3E32 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1A425741-58BE-45E8-94A9-40A7A62DA45C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FCA8CE97-5674-46E8-9858-ED82E15F33E7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D13ED23D-5036-4421-81EC-B8E3FC6DFD5B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F0D18866-686C-4B8D-B02B-4BEC2BB95327 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 110760A1-D2F6-4675-A1CF-675F7550C20A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 832A0402-216F-4703-92BB-43F632CD6FAF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9950F70B-EF45-4C10-B814-1441A8DA0DFD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 40943F62-6814-496E-8BD1-F45F3880B160 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CD200B6D-B064-403E-8A97-CEC6A8C4AED5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A8BC79BB-378E-4928-8A1D-6B7FB7D8D6D7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5E803C9A-3C5B-449B-849E-3BA2EF2B12B2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 98A375DD-FFF7-4168-98D4-6B219411B09A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C3B4A941-F46B-40CC-A941-91C8690C0A75 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F7638415-628E-4FE4-862F-3EDFA5C96078 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6DC61443-828C-4273-97CF-A7B26C37853C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B0916982-3C1C-403A-90A7-263BA74F3B7E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 01379F72-D401-4579-B14E-B1C785499AE1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D6D7B068-F22D-4A8F-9B7C-E0EBFE0BBA16 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EA8142FA-6A8D-4481-9331-B2CAEB5ABA95 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1465F5D7-33E6-464B-B6F5-345673D45D29 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 79C5C398-4C3E-448E-84B1-DA29838D913A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5F6DA10D-E6D7-4A76-A41C-21AF715137D7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1D90E049-2774-429A-BA6E-E9AE74163FFD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F8013D1D-97B1-47FB-A7AC-FFAE9130E032 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2024-12-10 '-XMP-ph:RideName=Nascentes da Brasilândia' -XMP-ph:RideDate=2024-12-10 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 19 — Nascentes da Brasilândia' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 19' '-XMP-dc:Subject+=PH 19' '-XMP-ph:RideCodes+=PH 19' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === S 3 — 1 foto(s) ===
DEST='/Users/danlessa/pedais/2024-12-13 - S 3 - Jaraguá Hidrográfico'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid E00DDA49-BAF4-4AEA-94E8-02F614345868 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2024-12-13 '-XMP-ph:RideName=Jaraguá Hidrográfico' -XMP-ph:RideDate=2024-12-13 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=S 3 — Jaraguá Hidrográfico' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=S 3' '-XMP-dc:Subject+=S 3' '-XMP-ph:RideCodes+=S 3' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 20 — 24 foto(s) ===
DEST='/Users/danlessa/pedais/2024-12-17 - PH 20 - Águas de Pinheiros'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 1E8CD236-8A6E-4C84-ACD1-8BCC124FCAF7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 62B0F398-1057-4B5F-A412-4A93B519A1E4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C5F768FB-5388-4013-8B66-2BEEB8E15D0B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CFAD77A2-813E-4A68-B3C2-390D9666E719 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FE2FA9CA-71A4-4BA4-8F62-E0239FB92CA4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 10378416-EBC1-406D-A981-79A39D692CC1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7E893635-6B4B-4678-9483-FFB237343C90 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EB6434CF-CCCD-4B9B-8F19-02BEB63FA8EE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FD960DB3-EC20-4CB5-9A85-14B13D76D5FD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C6FDADF8-7820-4C9D-A7F7-9FA3D6133904 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 577620B8-CB47-471B-A41A-99231AAFDFCE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B947885E-E2DC-44A2-B4CC-A8131A727A42 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A16FC979-C41D-4A34-8174-CBF63BC7E949 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A95E5075-1D20-462A-9759-13F084B53A78 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3D23FAE7-5426-4D20-948E-045F39964F2F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9D3781A3-23AC-4F0C-B2A9-2876CE523400 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3748CD51-9122-477C-BD3F-0568FD3C342C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0A1D736E-2A54-445B-B702-FC25F6185293 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 041DB242-20F1-414A-8CBF-27FE4C105604 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CB779FF8-E7BC-4E27-8BFD-2BD61E174500 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 33A0E7CF-D3DD-4D48-914A-2E86E5FDDBFD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0C107E5F-1068-4294-9B35-345AF186C2DE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BC68C390-D1E2-4F96-A9ED-152E3CAE3027 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D8CC11D6-D5E9-41E5-9818-4ED0A2D6EF3E --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2024-12-17 '-XMP-ph:RideName=Águas de Pinheiros' -XMP-ph:RideDate=2024-12-17 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 20 — Águas de Pinheiros' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 20' '-XMP-dc:Subject+=PH 20' '-XMP-ph:RideCodes+=PH 20' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 21 — 11 foto(s) ===
DEST='/Users/danlessa/pedais/2025-01-07 - PH 21 - Verde, Anhanguera e Sapateiro'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 4C78734D-E3A5-4BC3-A8C0-32C38AB23741 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 14392FB8-7933-4313-AB53-D339CDDAAADC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 442BE104-D135-4284-8D3B-79CF358F4B60 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 31B3AFC9-880F-4DDC-BC37-FBB359FA58F4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 18F952D6-07A5-4F8F-8199-996E61AB4BB3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DA951681-A84E-4926-99A9-E191D8E4257D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D8F7944F-DD55-488D-9BE5-B1CEBFD407D2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 87E49B16-66D7-48A2-BE1B-EBE6E0E79813 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5DEB180F-E845-4DC0-8DE2-54109A04E167 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 80667292-7351-4155-9A14-8ED944333B30 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C2FF5930-3F84-4DC1-9790-16B8FEC7C942 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-01-07 '-XMP-ph:RideName=Verde, Anhanguera e Sapateiro' -XMP-ph:RideDate=2025-01-07 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 21 — Verde, Anhanguera e Sapateiro' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 21' '-XMP-dc:Subject+=PH 21' '-XMP-ph:RideCodes+=PH 21' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 22 — 4 foto(s) ===
DEST='/Users/danlessa/pedais/2025-01-14 - PH 22 - Contornar Pacaembu e Sumaré'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid C424944F-F073-48E6-9B4D-EC01D23AF194 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4A33A28F-69F7-43AD-AD20-503370D4BF0F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C5CB85BC-433E-4DAB-A44C-C2BE18D1264A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E4A5255F-988F-438E-818A-F412E866E9FC --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-01-14 '-XMP-ph:RideName=Contornar Pacaembu e Sumaré' -XMP-ph:RideDate=2025-01-14 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 22 — Contornar Pacaembu e Sumaré' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 22' '-XMP-dc:Subject+=PH 22' '-XMP-ph:RideCodes+=PH 22' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === BT 2 — 1 foto(s) ===
DEST='/Users/danlessa/pedais/2025-01-19 - BT 2 - Foz do Tamanduateí até sua Nascente'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 49A0596B-658A-484C-BEC6-58EA2202D43E --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-01-19 '-XMP-ph:RideName=Foz do Tamanduateí até sua Nascente' -XMP-ph:RideDate=2025-01-19 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=BT 2 — Foz do Tamanduateí até sua Nascente' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=BT 2' '-XMP-dc:Subject+=BT 2' '-XMP-ph:RideCodes+=BT 2' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 23 — 40 foto(s) ===
DEST='/Users/danlessa/pedais/2025-01-21 - PH 23 - Crista de Sapopema'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 9C97E6DC-9057-429C-9131-CFADA43C4D2D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F995EB21-98B7-4B13-89B5-D9DB5727ED75 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 14F69CC8-DFCF-4EAC-8BD4-D47D086D7BC2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 96921CC6-DA84-4F4C-8C32-0F524814A217 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B232EFC2-7C83-4ECB-9EEB-E445C8BAEB3A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A6336543-0B9A-4B35-9FC8-F72F0FF27D3A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 683D09E0-6BD7-40BD-94E1-C6C7F634AB2D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6D9EEC5A-1ADB-4942-803D-D3AC78AE011B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8344B89C-683A-4651-9B94-D8724908D374 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 92B3D0C3-A9D2-4C4B-85AE-84F080C53A7F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 77093FB0-C43B-4AF9-A516-2A839DC9D517 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BB4AA547-CBCF-4528-A0FE-FC182F76BFC9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B74C6340-09DD-46D7-A150-2B881CBE2857 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 63D4F166-A54A-4FB4-8F13-48A2F148A641 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 10A8A0F6-552C-4236-8F3E-45AC20268BE2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 05DC268E-A22B-4013-B09D-1FD5096EC9EB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9B8B7D64-5376-4806-A193-CC1DD4F11926 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8DBDE53C-F55A-4086-A07F-492188FE8B26 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2A3235F1-7BAD-44FA-9638-5D8FB15ED732 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F9C3A91B-C15E-44BF-9F1C-F361F7FC573B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6DCA3C0B-BC69-45A8-937D-268D049CC23B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 783B48A2-7A12-4733-B222-9365D0F6D8BF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F6A0D1B4-C8EB-4801-A703-2162CE477AE6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6E5DD6C8-A48D-4760-9412-D4E50D490E13 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E98DC1A4-4979-4EE3-9656-5F9303E810E6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3ED5E29C-8595-4E8E-A786-90E7D7659B9D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4277A671-962E-4BEB-909B-0F7C0A42463D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8632503A-4C55-43A1-BD26-AAE5F7A6A0ED --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A2148330-5120-432A-ADA8-3AFA7908D232 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 09CF3153-AC98-41DF-B4E5-1D8B94232C60 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A12230C6-7DD7-4BBC-B93E-6A91264D96BC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 33BA8D3C-517B-4888-8934-25121B3FE4D2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E3859DBC-FCB0-4E74-852C-A8337E468D38 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 226D0139-B30D-488C-8A28-4F71834762A9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 32C5C98F-C879-4C9E-A97E-92C7C1D56284 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 74901B64-48E5-4E62-B90C-E2E38E9F51F4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C24DC440-27B9-4D76-B324-B20027093948 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C0740AE0-5403-4088-B47E-05409EC8F9F1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4A7D52A7-067B-4E3C-8A74-961F7C025072 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AFECA804-492B-456A-AA7C-A22D4107C75E --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-01-21 '-XMP-ph:RideName=Crista de Sapopema' -XMP-ph:RideDate=2025-01-21 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 23 — Crista de Sapopema' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 23' '-XMP-dc:Subject+=PH 23' '-XMP-ph:RideCodes+=PH 23' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 24 — 7 foto(s) ===
DEST='/Users/danlessa/pedais/2025-01-28 - PH 24 - Contornar Anhangabaú'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid F67A3E3A-0121-4784-A79F-B22240E4D41C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CEB77507-ED08-4974-88BE-D77265B721E3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9251BD10-700C-4ECB-8D82-1AD15A9188E7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 03B1280F-DC04-49B1-8FEF-3AFAFDE3F49C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B4648273-FAF2-475D-B183-4DCEC4893E46 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1B484DE1-1FB8-4E18-8CDA-2BD73767EBEB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 618BA0DA-AB69-4D9E-B880-203FD0EB1BCD --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-01-28 '-XMP-ph:RideName=Contornar Anhangabaú' -XMP-ph:RideDate=2025-01-28 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 24 — Contornar Anhangabaú' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 24' '-XMP-dc:Subject+=PH 24' '-XMP-ph:RideCodes+=PH 24' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 25 — 50 foto(s) ===
DEST='/Users/danlessa/pedais/2025-02-04 - PH 25 - Pirajuçara, Água Podre e Crista de Osasco'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 285F1835-B7E6-4AFE-8BF6-BE3ED99B0C07 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D8A86D3B-3714-4923-BB34-D60303D1EEB8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 815AA121-C8F3-4738-8743-508B71FC9775 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5D1E25FE-63D1-4265-A2F8-6C2C4F4B9E12 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 20D7D20F-E1F5-46BF-97C1-3A29BA9FCDF5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0288D1E0-A36E-4A6A-9598-8F1D2F7CE3A1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 60ACBA57-0491-451B-9654-AA7D4D1D6347 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 41ECC84F-8E2E-4CAF-9FFD-7A1777F3784D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4DABF651-CB34-4205-8946-341574450EBB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2C0A60ED-7CDE-4699-A4C6-906461559AC8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 26818447-4B83-442A-BA5D-DA7AF15A8743 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 06BCCAC6-F6A2-4539-9ED9-AE09524E7A6E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DFC5FC0C-ACE2-4BE5-816C-E69B25AE1F60 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 957AA2DF-1A74-4EE9-A688-6C2E20484BE5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D6BD40A0-B12B-4496-B3DC-88A7B1E01E95 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C7D3E05D-4B3D-4A5C-83A2-8B5CF8B098B4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AE403178-687C-4AE1-AD35-9B7C8BFF1FFC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B733B250-9EFF-4F77-AA0A-C33CE5F86685 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6EE73423-5073-4489-A8FA-1C63323686A2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 844FE9F6-C78A-446E-A007-77BB4C0254A0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6B746984-A5A7-4308-AD9F-4A741E5F18F4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E67E1F5C-C63A-4CBA-A4FB-5A06ADCBEC53 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D26660E1-B17E-4969-980A-82FEDF67B423 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E1CED991-5078-43D5-AD40-F4709E8C2F56 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ABE7A954-1BC7-4B04-B391-56C571658038 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1BB687C9-24F6-429D-969C-D51C0FA91196 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1152AF95-B8FE-4223-A8F0-4EADBE9296B0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 89FF33F5-F12F-4C43-8BA1-605F373CC3AE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 59AA2BBE-2A6A-40E2-B5D8-DAD8948FCE29 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 97353892-0E63-4EB8-A8ED-0408E23D1166 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2FB4D634-BE9E-4A05-A589-C0418E83C779 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 82F2D9C7-4BB0-4283-8588-9B3F09E6E6A2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 10F32212-E482-463D-ADBE-6E25703EB5F9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CAC7A76F-D888-4A68-BF90-4339036F210D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D3F76C33-0ECF-4C2D-B614-96A72F8AD6FD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C0549680-8549-47A2-B9F7-7233FF31D50E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B49CFC5D-D346-4529-9947-52FC2332EB84 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3DCBD286-4267-4532-95F3-A0F241678585 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 409C3223-7B19-4013-9E81-EC7AFE027EBD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2CB7B333-623B-49C2-9474-34D3937986BA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BA6F98EF-ECA1-4598-9BC1-5F2AFCF82E8C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F75E95F2-D41E-4F07-A58F-CCE9B8B3392B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 44882B81-2E28-4C8B-940C-D26B9640BF34 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7EF574AD-D5B0-4EE7-A1B3-1A750BD15EE0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 18CDBF57-9AF4-49AD-B81B-2297FEC61C3D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0442B731-6BA2-42E6-96FD-FB446C27363C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 24F441E5-708C-4F9C-AF0D-5AFB94DBBE4E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BC2DBB2A-1536-430B-8030-F8703E63C4BC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6C807D91-0D77-47AE-B40D-4D34BB307590 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 271CBA09-6503-45F5-91D9-62A5A62E78F5 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-02-04 '-XMP-ph:RideName=Pirajuçara, Água Podre e Crista de Osasco' -XMP-ph:RideDate=2025-02-04 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 25 — Pirajuçara, Água Podre e Crista de Osasco' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 25' '-XMP-dc:Subject+=PH 25' '-XMP-ph:RideCodes+=PH 25' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 27 — 50 foto(s) ===
DEST='/Users/danlessa/pedais/2025-02-25 - PH 27 - Sertões do Mandaqui'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 5FE87886-57DA-4EFB-ACAC-0A7164118C8E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 68445B48-B53D-4D2B-888F-CDE398F1CBE1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 951EC1BE-0B33-4ACF-80F8-240E7B80C927 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7BB77F16-DCDA-4B79-87A6-01FD730177A1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E9C4A93D-08F3-4C83-960F-D25453CE9D44 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3A60F9F5-204B-4CD9-A6FE-E520875BF869 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0F6A0066-6D8F-4BE0-BFE7-B8FE5382B2C5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9830D21B-9D3B-4889-9AB3-714A2FBB69C1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 331B73DD-A46E-466C-B6E6-4B5A03453807 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0756E898-D165-4633-9622-EF00F35FED4D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ECBE4B17-ECA9-43A6-AAAA-1E4E49B3F1DB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8B858197-0A71-49AB-84CF-007302CA9E19 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E0D9C939-C73C-4B04-91DB-30FB1DE4FE07 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FE18B935-A9BA-4DFD-8A82-3882D3A2300D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2FC0F6E3-42CD-4CAA-AECC-BD8DC0E92616 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F0549E0B-D5DC-49CE-91F4-05ECBF2A4A2E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8CAD4BF0-CAE1-41D5-9221-14A9BE0C839A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 171ACF57-1D22-4A57-9C8C-41333BA43634 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ED07B5C3-B2D0-4DBC-92A0-472B64BAE0DD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 592166DE-85F2-42DD-9837-8EB7BE184127 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CF26A01E-4FB1-45CB-B386-3D0EE43ADD02 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D8623AE6-49E9-440A-85E5-6939AD83ED2F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ABCFD878-62B7-4CD2-88D2-03633779B95E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3901B5FD-C85F-469A-B8D0-E2518BA1AB36 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9231691D-B04D-4471-9AC9-CBFFB95D99D2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8C3CED1F-40DB-4EFC-A8C3-73242B316EDA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0B60C476-4EDB-48DD-956E-090A3DF6BC52 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D5B115EF-6128-40CC-807F-48D895A82336 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CEF8CBFD-2278-4F77-8A9A-1BB3011A9B23 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AFBF8707-0721-4F9B-91B5-7EB7B51D70CE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DE9A8968-2419-4FE7-92D3-60E309B96006 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D2209061-5763-4EA3-81AF-C8C345046322 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 354295E6-013A-4CD5-9B4C-4CDFB06A8382 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 49EF8404-C4ED-4A61-B4CE-548B12981464 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F0BFAEB9-A999-4A7F-9B89-4B6C18E46BCD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A25F4B63-27DB-40CE-BD5B-6CBDAE6C37B1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 144CB57A-32DC-41C6-BE4C-8D01F4B4515D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DCBC10D4-D7B6-4217-85BB-B889EE1EC45E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3D8C2ECB-736B-4501-97D0-CDBBC876A661 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F2AB71CF-0B24-4B40-B362-7DD46076B25F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 40531CA6-65DE-461C-9FEA-24E57029CED8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9623C1A0-CEA9-455C-B420-22C6ECB249AB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5EB3A086-EF31-4891-9834-D5A28FE21537 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8374D0A8-A952-42DF-B573-540EB6FE601E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8D1FBC58-4620-4BAE-96B2-4917A768CDEE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C815A2E8-4E4C-4E4A-BD25-0E6C1E4AB298 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8468594B-B8CB-4A7F-89A1-885AE04B8B87 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F6B69A85-84ED-433B-95E0-6384EDCBC1E1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0D6620D5-B7AE-43DE-A67A-3EEF4AFA0048 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 357EDA2C-6597-49E3-9741-D786A2DE32E8 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-02-25 '-XMP-ph:RideName=Sertões do Mandaqui' -XMP-ph:RideDate=2025-02-25 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 27 — Sertões do Mandaqui' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 27' '-XMP-dc:Subject+=PH 27' '-XMP-ph:RideCodes+=PH 27' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 28 — 47 foto(s) ===
DEST='/Users/danlessa/pedais/2025-03-11 - PH 28 - Águas do Lavapés e Aclimação'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 94962DBE-4670-426E-AA31-18FA3F84FC59 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6C06193E-872B-4C54-AE2F-56F9B03ACEA3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8701A48A-9845-49FB-A29B-49C2967AB3D1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4EE87FAF-7C3E-468F-84B1-DC8850191B4F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 67B52CB7-242E-41B0-82BC-FBB1B428E9A7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2A637EA8-8FE3-47B8-9D0D-010FEA91B27D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 805CCB30-0762-4127-BB74-E0DB6F0E1A9D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 59443D4C-4F2E-4D75-ACC5-BB4E691935A0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8B024BC3-87AE-4623-9338-D70028483539 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8127B78E-2611-4721-B069-AA1C5C848A0B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 19790275-F81A-4ABA-90C3-644C3D1BBCD8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CB5571AE-5711-4DC4-B899-A82C60345AED --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D3575518-29B6-405A-982A-0FA12D53F038 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 375107F0-1DD0-46F1-8995-C7090A3A9764 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 624F067E-D83B-4A35-A1C8-C3779FED3524 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F7BDEDC2-0E31-4741-81DC-79F943F703AC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A86D8EEB-4ACF-40C1-A021-45F9336D4B3B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C13EF84B-CECA-4181-A0A0-E40D80E1EBCB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 980F84F2-2FAC-4391-AFF8-8C117EF90BF2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C526D747-1FCE-4756-AF4D-9FC92EAC1077 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FB6F486B-B686-443C-9A50-6326223258F1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D8501B17-631E-47A3-9626-B608779C07D5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 739E4E48-ED06-420B-887F-63D5BEE1FAF5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5D6E650D-E733-4EF6-8258-F8D710C8AFF4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A6467B66-C0CD-42EC-BEA2-88E02C633777 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A005FDBD-E086-4ACC-A968-5E70A39B75BD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 07096CE5-433B-4B45-83E4-21A2A92DF79B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B17556C7-81C2-4822-93E3-5910C5293E06 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E1065FCB-5936-41A3-A72B-AD9896988611 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B8454838-06C5-49C0-B2DE-D8E21180F734 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D3E3B2EB-5397-446B-82A8-B24FBB19580E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C95968DD-DFD5-4F70-AA8E-627A6A6BF19A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 193DF2AE-04A1-4FFB-A4F9-2EB469CD7BF9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2312B21D-C264-46C0-A249-6CEFC4AFB002 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A805B423-66D8-4DA5-B8C4-536F25700D38 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C6301363-CCBA-464A-90B9-39FAEF31CCF6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5EF3E87D-92E6-4A7E-8618-104F329D07BE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 75C8DE47-A844-4665-8487-130C3FA372D8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A3940B57-9A6B-4C73-AAD6-31BB8EB663AF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BA1F8ACA-874A-464F-9209-2DBD04B11A3A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2F1E1E86-F692-4247-888D-AE78C6547D75 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BC35F68E-AC9E-41C6-84E7-DF23D112893A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6263B6E0-CA6C-4467-B16F-4A4DD0C0326B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ED19B8A3-88D9-42EC-BA44-9FF966BE5246 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EA69EC29-5871-4FC2-B79E-91137BF83A74 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BE5ECB27-8CCF-4327-B638-17FDADD67507 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CFB18333-2703-491A-A458-490E9C3F09D6 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-03-11 '-XMP-ph:RideName=Águas do Lavapés e Aclimação' -XMP-ph:RideDate=2025-03-11 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 28 — Águas do Lavapés e Aclimação' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 28' '-XMP-dc:Subject+=PH 28' '-XMP-ph:RideCodes+=PH 28' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 30 — 46 foto(s) ===
DEST='/Users/danlessa/pedais/2025-04-01 - PH 30 - Subir Pirituba, Surfar Alpes do Jaraguá e Descer Perus'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 9A1F092E-9F2C-4A5C-9AF6-7C79F07A4598 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 493C3FFE-A732-4CC0-8E4F-F66C6E1D24D2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D5735F1C-2014-4FA7-8DEE-88AA0A8B56AF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B09B47DD-004F-4CC1-AEEE-6603AF2E6CB8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9AEEC93A-047F-4357-BBF3-299CA16EB1CB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5531F5B6-1D99-4136-B1FE-F6F49E07FBFA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7C134501-37CC-4575-8527-BCF8AC06C690 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 508B3DD9-3D35-4869-858C-515C175A710E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3B1918B7-49AA-4A1F-9E90-6E520D15BF56 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ED9F00EE-F7F3-4F5B-A8F8-C5016D3CA2F4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8EC34F91-743B-4A54-A5A7-405583DFA8EA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2C01E026-0BDB-4FCC-B077-817E75DCA649 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B937B8D4-C3A6-4E2D-B640-6211534CC9B3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 761D5DF7-62A2-4AFF-9C1E-F6D57B660552 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 461EA574-0868-4113-AA47-08B13EC9CCD1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6C6C84A3-7539-4EA0-B7C1-39F43B84CEF8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5EC2926F-D104-4262-BE5A-1E0B941AAEFC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 856CA345-F78E-44F4-8974-B4E5170C3315 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 78DE1255-9890-41A5-9DE6-768884D4ECD0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 75539063-95B4-436A-A892-7555ADEEEB91 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0F40C0A4-962C-42E9-ADDF-02925A1A66BF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0E7B8E38-A15D-4CC8-9C2E-50A40A2104F4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 55CF0055-F25C-47A9-A8A1-AECF3B5AC143 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AAE2BCE8-AB61-4366-8E1C-F00C4D03709C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1EC4FDBF-508E-4E08-BE0D-D4B859153378 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1FA9A436-F03F-4445-9DAE-0AACFB7116A7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E37FC0F2-41ED-47F7-82EF-66ED644BD540 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FD37FC49-5900-4CB0-8F71-4C7AE94CC49F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 01ABE24E-D2DD-450C-AABB-D560994008F2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 21CED3DE-FD5A-483B-B8A0-5C4EE62EE130 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DE2C9C84-69C8-499F-934A-4EB54FD6E975 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 857A442E-0E02-41C3-AD23-F4186B885902 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CA180E84-3D5D-4177-B505-56988E45D669 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DCDCDD8C-23F9-4276-890E-74DC7809CABC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F7AEFF80-074F-4F24-A9B3-333F8801A7A0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9486BA8B-7830-4199-8C4F-3EEBB35C1A04 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B9269285-A8FC-45C8-8BB5-C8C40889ED77 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3B346014-F895-4016-B613-E329C7846705 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 163A23D4-5009-4FCD-A54A-0F31E732C378 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D97F9ECC-AD28-469A-B73A-C4FAE7158F99 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 90BF29E8-358D-48E0-A347-852B734EAF25 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2109D6F3-9573-4DE5-AA40-A73682040E7C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6D03EFCD-B5E7-47DC-8E47-FA05AA87B5B4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7D3EAC34-4650-46F5-9FE1-89FE8DEBE6A3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7F056343-17DA-45FE-8053-11100ECD6B6B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 80B3A753-3644-4043-A0DA-C0CFAD9CD883 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-04-01 '-XMP-ph:RideName=Subir Pirituba, Surfar Alpes do Jaraguá e Descer Perus' -XMP-ph:RideDate=2025-04-01 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 30 — Subir Pirituba, Surfar Alpes do Jaraguá e Descer Perus' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 30' '-XMP-dc:Subject+=PH 30' '-XMP-ph:RideCodes+=PH 30' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 31 — 39 foto(s) ===
DEST='/Users/danlessa/pedais/2025-04-08 - PH 31 - Tiquatira da Foz à Nascente'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 445E699E-3F65-4512-8B1D-2C4E0D8F6B8A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9AA3D0B2-9798-4E7D-A65C-314A78E792FB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B781E9BB-1C98-4386-9DDA-B90F72E55FA6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CD6EC7DD-AD19-49B9-ADED-540A4223C1E9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C72C5D5E-2C51-4E4F-8EE7-BA5CA3F01C72 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 97D70ADF-2023-4E3B-AC06-B300830BD862 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 034827AF-8A51-44CA-BEE7-2AA44FE874BB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 400D016F-D5C6-4170-9096-64E41E66555A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2819C9AE-1548-407E-B991-46F8EE14E4D8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E0A36E64-CC74-48F6-8C4F-A92E1AFDE65E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ACEC34C0-D390-4143-AE99-87AFA7AA270C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 27064B87-C4F7-4EC6-9C6D-A81EDACE4960 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B8B101E6-3A61-40E7-98B4-3817C934CFE9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C55F034F-9991-4040-8F1B-F2BA75C1FFA6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 03AA9E8E-977D-437A-A98B-C6B6E8436051 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 71277481-CD8A-4009-BDE1-438BFBBFA19E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C6136A31-5BE9-4F83-873B-1D436790D715 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BB727AB6-5300-4F55-B395-72B221D31965 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F78790E9-2539-49BC-8EA8-6EA1A4EF7213 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D013A5E8-6EA9-418F-8A94-B152C52607C8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 82FA4CB0-8B68-4D53-9F27-08C5E9179D83 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 932AAC66-DA6A-434A-AC2B-0242A40B3657 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C9719CEE-D18E-4D30-B9E4-D82A14B64FCE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ADF7842B-D0F7-49D6-B525-77D07775C645 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B718B023-B4B5-40D9-899F-9BB90AA750B6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DDABED4C-85D6-4DCC-B6D0-AC7B96A0FC7E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 13D60B3E-0D7F-47B2-AE62-8DDE60F6F2E7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CE54C71B-489F-4DB2-B7F1-8719A124AB02 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CA3ECB12-1723-4AD1-AFB9-98113BBD26B0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0EE9AE46-4574-43F3-9A90-4CF68112B36E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 15FA7884-9E93-470F-B4A4-AD9FFCE125CA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A057BF4C-3623-4D38-A95F-1E2E6AA10AD5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CE92CE2E-3905-45FD-8BE5-11E7C41FB2E3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C5EE34C9-F989-4409-B52D-204EB6372282 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6666D557-F7E3-4CA1-8530-DBA70DFAE1C6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1082BB5F-CE86-4E85-A895-3B1E72F98E24 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DD468D9F-46DA-4412-82C0-1DA8E7B366D1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A1DC35FB-E5F8-424B-ADBB-5AF7ADCE6819 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F9481A6C-C8C8-41CE-B853-5C14F8C6E164 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-04-08 '-XMP-ph:RideName=Tiquatira da Foz à Nascente' -XMP-ph:RideDate=2025-04-08 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 31 — Tiquatira da Foz à Nascente' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 31' '-XMP-dc:Subject+=PH 31' '-XMP-ph:RideCodes+=PH 31' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 33 — 46 foto(s) ===
DEST='/Users/danlessa/pedais/2025-04-15 - PH 33 - Moinho Velho A Outra Margem do Ipiranga'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid EB157B5C-9DC6-4C96-B326-CACDA6B52E4F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B5C2BE58-CA74-4106-8DFC-23C2D42B692B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5511E015-AB26-4AFF-80D5-1F85F614A02E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 44AE92C3-CD11-4F36-8504-0C94EF8CA302 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2A88C43C-BEBB-422B-B5CA-1CFFD53C0BB8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 35B92766-3302-4773-A69C-2FB74FBDC57E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3166FB80-7EC8-4E9E-B008-0218334FF8CA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A713C527-08F6-4BEB-8312-CCF78FD31774 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1D9CE124-2C6E-4C2B-AD71-9D1FADD9D85E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5B30C87E-C940-4DCA-A5C8-3BF3740331AB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 39C0D2B9-E7E3-4333-857E-F6A7F4D2CBAF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9F05D80C-5E2F-4DC0-A2FD-AA064F681FDB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 05D99FEF-DEED-42E8-9458-D8F10F7BB240 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2209663E-CF16-47F5-B95A-C7005E02C1A5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DE16C99E-21F2-4C85-AF08-38CD75CE6526 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D0B9AFF0-395F-4FED-BCDE-BDC4B29ACFE0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 50BC3520-FBFB-46AF-80D5-1AFBC0B17F2B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6FC39792-CB91-45B2-9E73-1680830915F1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4A77CE03-516C-4A79-85D7-455426F6A78D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6D6427A6-33B3-4BF4-8117-F8811235248C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E77C9D7C-212A-4C99-8400-704E48DF8883 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8CA25627-108B-42AB-A7EA-D8AD726AC0CD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4C66DAEC-61DA-4177-BD12-4BEC52973994 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BD6E3D42-0A59-474D-A80C-C96154058B57 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 92B9A445-BA36-44BD-B581-4829C433701C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5BDBB2AD-E505-4BE0-AD20-8D7CBBF7CDF0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ABB55DEA-0FB9-44E7-BC5E-0F5BB2B998D5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EEC7827D-B853-4371-AB54-D7373A966143 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 18A7E0B3-4530-4989-B1A1-895CCB125ADC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E5C9752C-6522-42AF-9148-F3F8558F8DA8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9708C477-02E4-4F6E-BF35-3CE110253880 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 669458DB-C360-46BF-96C0-A23F1883D2E7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D675A5A1-1315-4898-AA1D-D7237D7CA24A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E8353077-37D0-40E7-8935-5DBB5A16079E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1AC2FB06-1D60-4EF4-B7F8-C2E3C9A58719 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 44FAC346-43FE-4255-9A7C-83F07E7D935C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A3538CFB-1D4E-49AB-8781-C0FB17784CCE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2A9BB904-87AF-4360-96A0-C2F0E8987003 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 85359984-6B16-4861-B005-0DB009525F3E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B9360036-401C-4414-839C-9E006910384B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 13D18897-BE11-4945-9267-F62DE7312CA2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D3B3305B-7C64-45A1-AC33-2087CBB377E4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 75CB0922-E38F-43FB-A1D0-041B7B3CC39F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 928B54D3-0360-4389-BA92-3AB30925D805 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A03C5352-E260-4DBD-B9CE-EB3899A59714 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FDA039BD-62EA-4C46-BAC7-EED5F85F0207 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-04-15 '-XMP-ph:RideName=Moinho Velho A Outra Margem do Ipiranga' -XMP-ph:RideDate=2025-04-15 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 33 — Moinho Velho A Outra Margem do Ipiranga' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 33' '-XMP-dc:Subject+=PH 33' '-XMP-ph:RideCodes+=PH 33' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 34 — 27 foto(s) ===
DEST='/Users/danlessa/pedais/2025-04-22 - PH 34 - Crista do Campo Limpo via Corveta-Camacuã'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 7766BA39-3A5D-4E01-838E-47553F5F7852 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F990C27C-6819-4F2A-A444-3A05921D3811 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 40E8A31A-42AB-45A2-980A-AA3F120593C3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2B228B8A-C220-4836-95B9-B356EE38E2E9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9A7E3FC3-6A61-45A3-AA2A-F84E7AADAFE4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B7EDFE1B-3EE7-4940-9D4B-F88B06D2FC79 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F2130347-807A-43A8-946A-58393AC13AD7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4A4C2B11-B4A8-4EC2-87D4-B6558B54BA80 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 97AD154F-E52A-44C8-9C32-3A2641FF32FE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B2558619-C712-4F36-915D-6AC9AD0B6285 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5C814D00-A9E3-4F03-AFE9-E6C391EB4795 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DA3F60E7-803E-4195-872A-46E7EB26A092 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 890CE31A-3252-4333-A494-793AFAEFB437 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B6FD06F4-056A-414D-A82C-8F56273B2BA0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C5852164-9AAF-4162-8A72-F0222FE93E87 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0826F653-AF9B-4FA3-B616-31F59E787714 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4EC5AEAE-91D7-4A61-858B-FEA52B04601C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 15FA91A3-8219-4A45-9E5F-770DC2DDEAE7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 17FC708E-E6A9-47F0-A2E5-3BD1D0F34AC9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 95B3DB35-EC07-473D-B1A7-701D4B67AC6D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9C47BC70-B420-4905-8680-B3F279C325D0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D4BF6CA8-91BE-4FE4-9DBC-39C9B62B5300 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 167ECB31-C8DF-492F-9EA1-DF2B6BB05527 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 202FEF89-3043-443C-A472-8E30C11BC952 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 353CDCD8-A7A1-47F5-9CAA-FA0EE4CD8981 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5E78D5F7-55D7-4ED9-9863-19D904EB4F15 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 179E079E-C369-4C78-BDEE-D679C53B719A --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-04-22 '-XMP-ph:RideName=Crista do Campo Limpo via Corveta-Camacuã' -XMP-ph:RideDate=2025-04-22 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 34 — Crista do Campo Limpo via Corveta-Camacuã' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 34' '-XMP-dc:Subject+=PH 34' '-XMP-ph:RideCodes+=PH 34' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 35 — 94 foto(s) ===
DEST='/Users/danlessa/pedais/2025-05-06 - PH 35 - Os Vales Secos do Tietê dos Remédios à Osasco'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid A247B8EA-A329-46DB-895F-AB85F68ED22D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3ADE0C4F-09D7-480F-AE83-B79DE2C7F4E4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3CAF7B9B-060D-4695-881F-9E4E4065D376 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6701076D-DC62-4F98-A1CF-AE36DB9ED1AF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0B2E3E5E-963A-40D6-9226-AE8ED1690CFE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 51BDA719-92EA-4868-9A56-043C04683702 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CBA39A23-D235-4C86-852B-CDBE2EEAE2FA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 40BFADAF-13B4-4C90-AD50-402CA453613D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EF1EA037-69B0-491D-9DE0-6CFF6FC30344 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F421576A-0576-4899-A17A-4447123B9DB9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E4CC4729-9C03-4955-AE88-42691881D49F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8FF7595A-DD52-4A8B-9604-835FCA13A6CC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 096A7791-97BB-485B-9124-5443D48DE2B4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 02C62854-D1B7-4FB2-8AC7-CE8A5C002D41 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 056B1CA3-5387-45A9-B4B2-44215D1B624B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A2F33FBF-D57C-41D7-A9F9-7FF9DB033419 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 55325F4D-7B71-457A-B967-863BA02BFC87 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ECED85CE-A52B-4C86-8B2C-475141F78959 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B5AB9384-B8E0-46BD-B8CA-61B979C3C4AE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A448BBF1-C91E-42A0-BF82-146AF579E9B4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 24A82BF6-887B-46C4-9FAC-E7322384A013 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3C3AA00B-9FF4-4D19-9FB9-A98354DAEF2F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A24646D7-3AB4-40B3-AA7C-7536C6549EDE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 400CB0DB-28AF-481C-B905-B2BCE53AE310 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F08AB5A0-E82E-4647-A54B-C7D016A212A8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E22B619B-3A65-406E-AD50-5A68291EE84E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5973546A-2E8D-4806-8800-2986300B4BB1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A8B29E55-3171-472C-ABDF-402F2524EF0E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 42E16E0A-4859-4FD6-901C-D2800ADF832A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2C178978-A285-49F7-85E6-A2E1BECB7E38 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 980199A0-1BBB-459F-96DC-D67BFBD7908C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 226815DA-ADA7-47F9-AB98-4F7A18C5F1E5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1F245D36-A0DA-42ED-A929-D7DC22328859 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 19B18F8E-590A-46CA-B285-431FB3E785C8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FD0AA10A-0801-44E2-8113-BF925B110FA3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 24710597-A1EB-466C-80FA-D8D0F0CB89F4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3B4E81B8-5338-40CF-833A-831564B84AEF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F09F3FBC-A77A-404B-AD83-C3CCE60AFC9D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A795E078-3FEA-4675-9B7E-D6E8ED6AF502 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5D4275DF-1C4E-492F-9D1A-699C0CAFDDF3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3E81229A-9881-424C-874A-F86DED33A7E8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 25983B96-B455-491E-8087-30A825FFC1E9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7C59CC41-909E-440B-8391-62595B18A194 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5B563819-4A71-4D0A-993E-89B3CEDF789F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7F699175-5EE4-4CE7-B4C0-D204E4BF68A0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DDC5C94E-0214-4FD6-B27B-3FA01B80B1E2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 98E62D6E-9B9B-4C64-99DD-859A87047058 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A8B08D4B-B2CB-4823-8840-E75A131BAED1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 95CB2F9E-75D6-4ECD-9CE6-8AFAEB38DD86 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8EA781B1-2467-4DE4-B1EB-8D4CF46639AB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 51BABBC3-7CED-4D47-84E0-3C85FE294953 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BD0FF883-B6E3-4910-9ACA-DA7322EC7AEC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 89A5F74C-64F1-4B49-B6B9-2E11A3403A3A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BCEACEE2-BE8C-4DC0-8E33-AECCF81104A9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E282E7FF-B158-4415-801B-590615B61143 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B4A486E9-9AF4-4DE0-B589-B34A63FD6BD2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 888BBD4F-90E5-4DBE-B3E4-1B9E6AF4FE19 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D1F3BEF3-51CF-4A94-B983-8EA2AB7AE8F0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 33608AC2-7950-472E-A920-99209D3163B0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 761B556E-8CD3-4C39-B710-00018133575D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AC53BD2F-4BD4-4930-B54E-70B1A7F1CC5F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1F88E994-34D1-460B-9C1A-906B0B7D8C30 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 805A3105-3153-46A5-B639-BF5FDE532822 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 885E3CEC-6437-4B60-A21F-C5B4F5BF8C9B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1AE1EFD5-BFE2-4D79-94B4-0C6BADBF311A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3D488F06-D50F-4C4A-9DB7-07F278574A2C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BAB29E9C-638D-408F-88B6-EF51724DFADD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 995F542A-AC19-464D-A842-27AED9A6BF96 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 16028423-8BAD-49F9-94ED-C9153264262A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6C7B6D3D-025B-4958-AEA4-5DBC089DF4F4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7281244E-5C1A-405C-A0A0-DD1AAC45BDA6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 90DE04A0-777D-4F8B-AE7E-C652B3F365CF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 589A74D0-B54E-4911-939F-F79613949927 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BE761C25-B5AE-4F1B-AE4A-B1C27A901F29 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D3F16C78-0AD8-488E-8198-247B4B4E000F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0EB02DA2-F9F5-471A-98A7-45AC17F6C85A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FC51CE4C-BF53-4658-B7B5-B4E79D58C154 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 363B31D9-2674-45E1-88FD-D7743C9B1A17 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5B45EC0A-A494-49E3-9E2E-189627AF71D5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 77B53856-81A2-4DCD-A2AE-1FFC70453E23 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6956D691-953E-40C7-85BA-5733478761BE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4F0A69E8-6849-48BA-89D1-9132F071B362 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 078BD06B-77B9-47FA-ACAE-71658EAD5A01 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B5601721-AE61-493C-B725-658DB6F3ED7B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BC2E84FC-9557-4313-8EA8-4AB856671C76 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A5DF2CD8-3406-45F6-9791-1B04657ADFBD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F9AE36B2-9B0F-4BD5-B9FD-96F16710FA0F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 134D8D57-75DE-4572-B23B-9023B7BB6F7E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1F509FF7-2E93-49E1-948E-A3EE7BDB5B1B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8A0C0C9A-3A2F-4F63-9CED-512D1DC2F060 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6E16D81F-D432-4E0F-B049-45BB857E1DF1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DDA3CEF3-90FA-4E28-918D-32B41FC793A4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9861B886-358C-4160-BBCE-5F57C1966BDC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D573259E-38AF-4965-BB8A-09134099C3AE --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-05-06 '-XMP-ph:RideName=Os Vales Secos do Tietê dos Remédios à Osasco' -XMP-ph:RideDate=2025-05-06 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 35 — Os Vales Secos do Tietê dos Remédios à Osasco' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 35' '-XMP-dc:Subject+=PH 35' '-XMP-ph:RideCodes+=PH 35' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 36 — 8 foto(s) ===
DEST='/Users/danlessa/pedais/2025-05-14 - PH 36 - Sopés da Cantareira- Alto Piqueri e Tremembé'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 22D4207B-6017-43AC-9682-CD43E0A56E43 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 20BF8048-0F02-43BB-8965-58A54A0DD48E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7C757569-DFE4-40B3-89FF-A0D96240E84D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C2964886-D5EB-4A3A-99AE-B41BF4B03087 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E3CCA032-0261-47D5-90CA-ED48D4A7FE0C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3F27DD8B-7D80-47E7-9000-A29D7D8ABACC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 102B56BB-3973-4969-B305-E32DF0A1B809 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1D0B5AB6-3405-49BE-A673-6FB463B57689 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-05-14 '-XMP-ph:RideName=Sopés da Cantareira: Alto Piqueri e Tremembé' -XMP-ph:RideDate=2025-05-14 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 36 — Sopés da Cantareira: Alto Piqueri e Tremembé' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 36' '-XMP-dc:Subject+=PH 36' '-XMP-ph:RideCodes+=PH 36' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 37 — 79 foto(s) ===
DEST='/Users/danlessa/pedais/2025-05-20 - PH 37 - Sertões de Pirituba 2 Margem Esquerda do Verde e Alto do Morro Grande'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 083383FA-8317-4A76-893E-E1279397B2AE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8239453F-FB24-4BE0-AA8D-D26646F09237 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 720A97C2-13AE-4E08-AF33-B47158DC1F90 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DC9CCA7B-85E5-4504-8618-21B552E0DD24 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0BE61AF5-EC87-42E5-9DDD-5454C3F02672 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6156D70B-2142-433B-BA1F-B8B33C099D71 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 88038F4D-5919-47A6-B2D5-E75F41D06334 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FB3C9863-6CB7-46DD-A41E-69BBB9A4FEF9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 26607D87-0BF9-455F-972F-D877DF3DCAC0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FA386A71-26BF-4795-BC8F-DABC8CAB36A9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7456E28C-DA20-4823-8D98-52C437D9A73C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 85D22CBE-FED7-4429-BA11-230C6E53B8BC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8DBDB2E0-829F-4C1B-ADF6-DD30C21783BA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 64C7D64A-1673-41D3-B99A-6D7C59787BD0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9F80C121-B337-4826-B958-967ABB0D5896 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6DA86411-AFCF-418F-8AF3-60FBA7FB6939 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 15680519-CF2C-46EA-9473-3AA4CFDDBB8A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DE4E32E0-E15E-4373-9FAA-3FA6752ADEA4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A88A5CC2-9ECB-437C-8593-8D27FBFBF157 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1FCAE1D9-A2E1-4254-8E11-1F71A50CF955 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C5D9B30D-6EDE-4F59-9AA9-4BC7CB205683 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FBAA2049-35D4-4427-9A67-D5F2565F962B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B7B77E8C-F1AA-4483-B746-11E1ADAEA6FF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E7AFAF8D-98D0-4B49-8A78-ECF1CC91F76B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 300C34F7-E84F-4503-B618-604969A497A6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7E975FEC-ABE3-4CDC-A8A8-A68646F35D5B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BA31CB4D-C03E-4D42-914F-BCBE8062DE56 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 73ACE262-9BA3-4C18-8C36-AE57B3906EA0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CCA46378-0DDD-4F32-B365-6490A238E882 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 74A6F0AF-4201-4EC0-85EC-79041D02F721 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7A10F613-5E86-4FF5-89C8-7592B6AC575B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AD9F9115-BF49-4560-8518-C464659CF450 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 36E5CF68-4162-4C45-968D-3D485D212FC6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EBC0B24B-D575-4040-8419-C69807A94E61 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1DA0E0C8-3763-49A9-A33C-D01A82FBB79F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 49475890-4398-4112-ADF6-D0B69BBE344F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3D14D4B4-4DF2-4860-8D8F-FA59CC3837B7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0586E4F0-67F6-4AB0-8F97-D9D2821095D8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FC775C1B-5F09-4DA5-B26C-7CDBACE87221 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6EE17238-AE26-4841-8777-476FEAA63CF9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D6885481-4443-454B-AA2E-2E7A305710D0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C0C269A4-4EEF-4B48-9D5F-F49BBF763D8B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6B2B2BE2-A932-42D4-BD10-E889700FAA1D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F0005965-388E-4FC2-8C40-8B3C43E6C4F7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 362CC00F-0744-4229-B48B-49D8E3AA1B78 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8F94F091-9C84-4521-BFE1-6F35A87C02FA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A4654410-F588-49B0-A30E-A73D5809C730 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2B55BE81-6ED8-41F0-B8A8-DAD864386DEB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 39C43AD5-F50E-4A67-9A0A-1F39CE948112 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BE99112B-3520-4B9D-966C-EC75DD6971AC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A50BE9CA-921B-40CF-BB43-3009AEC407A4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 709B8B16-32FA-4364-A7C6-36FA19D191F2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A4C6E831-32A5-4EDD-A789-8256EE2750D8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A600D85A-5CFB-4504-8CA8-C7CF0116F745 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3DADFAFB-3A50-4F98-A98A-23298D31CBAA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2C508401-6C6C-48A1-ACB3-0D58C9D18971 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6133AF0F-86BE-4CF4-8A6C-9E03F24A5BC4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 392813B7-E814-4C1F-A2D0-23CD41DAF903 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F4C9BD74-C9C9-4C3B-B7D0-87C3AF5DE9D5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BCE0DD7D-A5C0-40FA-81C5-46F00D8DFF18 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D1C453EA-FA12-482A-9CD9-9E5F10526CCE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3561707D-670B-40BD-A142-1C89DF7E2083 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8DA24972-0E28-477C-9F1A-934B1F186D99 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4E0B0D14-EE47-4246-952B-44562291D4D3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 821628A5-61A2-4DC3-BA57-CB8D4745B6C2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8C97FD70-2ABD-4C1B-A58A-71E9EB01F2E7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 96E98294-72DC-49C0-8356-5F8B8A128A77 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4A51978D-CBA7-4C81-BB40-6F0D1470C1B6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D302646D-EA69-4E59-A05E-31A3611353F5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 63D857A7-B5CA-4423-ADB5-FD31EF1EEFCC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 77A48B94-0C38-4876-93C4-02F7562776E9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FB92EA08-0D1A-42DE-BAB1-7BABBFA9D41A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 696C443C-7847-4817-A1B7-BBA72957041C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 75BEAC6C-9E81-4A63-B56A-5CA490C08EF4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 551EC783-ED29-4AD1-89B4-3A854416785C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D425F363-1FED-4AC6-A845-F40CBC90354C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BD143A66-0F36-40DF-BAF1-6089C32FF3AF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 20DC49D1-1531-44BD-9A64-C1B8F9656BC3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6FBC7FB3-8E64-4BAE-BD44-B98FD7307B12 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-05-20 '-XMP-ph:RideName=Sertões de Pirituba 2 Margem Esquerda do Verde e Alto do Morro Grande' -XMP-ph:RideDate=2025-05-20 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 37 — Sertões de Pirituba 2 Margem Esquerda do Verde e Alto do Morro Grande' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 37' '-XMP-dc:Subject+=PH 37' '-XMP-ph:RideCodes+=PH 37' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 38 — 61 foto(s) ===
DEST='/Users/danlessa/pedais/2025-05-27 - PH 38 - Pontos de Sela do Centro-Norte'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid E45B4BDA-15B5-4E63-87A2-D098943FC24F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 826F705E-91A5-433E-B909-8C7672726470 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D6E848B5-9769-40EE-B065-F913EA1068BC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7FD5A3EE-3F99-40F3-9D25-D06CF852967B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 80743075-5600-401C-A749-F3F1DAF01113 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4B8C8D60-3D8A-4B5D-B937-F5297D759E28 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E913BEAA-9A8A-4D8C-89B5-A68871E3B3CC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E4299EA0-0629-4DB8-A21E-9DCF5744C8E8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2625DE49-6F6E-4FFB-8EC3-771E0CC29F5E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3CF3246A-787C-4731-ACF9-0B0CE434EA39 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 59D72E48-43CA-4BD0-A50C-0FB36B5DBFDF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 529762AB-3ADC-4DF0-A802-33338C712E6C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 014BC61C-DE0C-461C-BD77-E314F73F0FC2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7BA3E4EE-04DF-44A6-85E5-784143BBE507 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8CCD4601-9800-4B82-AA4B-AE46B59D15B0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E3ED8AD9-B647-4459-99A0-01B4146F328C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C7BEA41A-99B8-4ADF-B557-75677F579D1B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7F2E3C64-4105-41BD-8A57-5C0CE2AEA95A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4B9418A0-FDA3-4C9E-8C09-AC9F837D8A93 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 200D4799-8144-49E8-BCDB-D34BBD46F68F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3529EE95-441D-417D-A3F9-1C41BDB96B1C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 23C8785D-E246-4C39-B9BC-B0045FAD3405 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5A0B85CA-CEFC-4DF4-BC5E-C306C7012CF5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2213FAD0-387D-4139-ABC7-F7564E27AA91 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C9A0978B-28C6-42D2-B499-41706F4059AF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 41878600-0B03-4428-9B05-E9441B944546 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 03BCE1E9-5FF5-4A63-B148-ECF21DD633DB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 00FEC9D3-7516-4B1A-BA6E-15EEAA713277 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2C4CBBBC-A304-4495-8B42-3CAAC749621B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5645AE25-B027-481A-89B6-3D3F26CC9EBB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C4F0BA6F-E0FC-4FB8-914E-F76F8A485F63 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5D7695FA-5222-4C25-ACF7-8A9771B019C5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A55F589F-3647-4BBA-97C4-D591741971E0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CA9D9B92-F2FE-4A35-B825-A51B59478392 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 03752082-164E-4B0F-9310-FC4B6935F588 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7B5153FB-77C6-462E-8C9A-2985716DF4A0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A6814ACB-014A-4100-A910-6FD327F9C105 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B9DF5CC6-383A-4912-BDBD-5DEFE0EAD2C4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 41018A28-D69F-4AA2-9919-4A41A303F56F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 57343F71-6BBA-4B68-A50C-918D10B4473C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B81C3B05-52B6-409A-A6A6-D73FEC64E17C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5E42B863-6F3E-4017-88F7-0A1A281D10D5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D3C62763-9F3E-48E7-9C28-8DA1A1D1A18C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D3ABB09C-515C-415A-8EDC-4B9366DF6A58 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9B920B49-2F47-40BD-9AF0-D65D9892A06A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 86453CC0-D204-4770-B01F-708365FB1572 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 60559FF9-4D79-43FF-A8E3-B951D9946DDD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 07FE47EC-688E-418D-90F1-C2B9DC66E35F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8B6F2415-F443-406D-9FE9-0EE6016E1C1E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 77D1426D-2A3D-4AD0-AD25-BA4CC3D563B4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EFA96C1A-50D8-47F8-A708-B33DAB31C8AA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4EB99ADE-A44F-4506-91D8-DBCD34C81CBD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7F192BAA-9E6A-48C1-A592-4B406320F99B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DF0247DA-00BE-43AE-81AF-1B3BA4B24562 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A27A47A1-0DDB-440E-A5F1-0BCE94F36F46 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 58C282E7-6F30-4073-8DD0-FDA355A569A6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B042A24E-945C-46BF-A280-8A50453C9AC6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F2C2485B-B0FD-4942-A144-C558C0E989FF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9C955CBF-3FB0-469D-B1E9-8BDBBEC2AF72 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 846968C9-12F1-45A3-8CBF-B70712414197 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B1BA6625-A196-42D6-81D3-4112F5C76A6B --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-05-27 '-XMP-ph:RideName=Pontos de Sela do Centro-Norte' -XMP-ph:RideDate=2025-05-27 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 38 — Pontos de Sela do Centro-Norte' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 38' '-XMP-dc:Subject+=PH 38' '-XMP-ph:RideCodes+=PH 38' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === S 4 — 94 foto(s) ===
DEST='/Users/danlessa/pedais/2025-06-01 - S 4 - Cânions da Brasilandia'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid A9DC98A7-D956-4668-8FC6-6CDF430F35A8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6381EAF2-8007-4390-9E1F-B7FF95C26D9E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7B8EE6E0-615E-4949-8AEF-4958D8AE0A1F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F35D517C-473F-4FA9-BD5D-5474F957B861 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E3779725-AB69-43F4-B2D1-794D8CFBFE6B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C86A7A68-3C3D-47CC-BBC4-62AFC953E1D1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 50028785-86B3-48F6-9DAE-025AE421C19B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B80EE414-BCF8-41BC-8FB2-FB51AC2DC90E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 334919DD-6B09-4E37-B224-22DABA716D0E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 63F53D76-5E0F-4139-AD0A-21898851E00B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FDF92EDF-A6EC-470A-A3DE-A5045CB79837 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9CB83A31-44DB-48CF-911C-DE30A7F0F599 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D93AADB5-F6B4-43C8-9439-EF540D1AC96C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8EC80A4B-5D07-429B-B6B0-FBC085660B60 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BA706D53-38DB-4985-B3D4-1B624F774A76 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 24C7CAA6-C0B3-467A-AD28-7A7C3607731A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8BD9C69A-E64B-4A06-8DCF-DA2CBA25659A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7E5B4A1C-E762-4A34-BE54-C2AAE2A09101 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 27E1A22D-6C78-4040-86CF-D69C02C30BF2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FACB3803-AFB1-4EBB-B29D-30A4DAB01EA0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F68AFCDA-508D-47FA-9CD5-F60242163C67 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EFBFF5FA-D726-4491-AED4-ECD9FF266C70 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0761452E-75A4-4A8F-AFD5-D27AE308971B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 691488B6-481B-4185-B367-F2A076112187 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2F1CFE46-C8E2-40E1-B7AC-4BBD4A245BE3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8285ADC6-C172-4B2E-A9CB-8A441E5843A8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5BC29770-8D0A-4AB4-8DBA-D4641AFF6D9E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 664DF267-CFBE-4ACA-B15B-AD72AC156AC2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9001E85A-9866-4568-B908-980DA369F731 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 563CC2B6-8A10-4B65-9F73-84CCC94759A9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B14AF9D9-A39C-476A-B464-73E08B5BF3B6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C4D08EFB-8671-4B16-9FCD-44541AE8B5D9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2834F05F-BEDD-4F39-8F8B-BB41F6D72265 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 885CD5AE-C252-418A-873B-A95F568EBE45 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7046B85F-BEAF-45D3-83A4-A5E48CDC7CC0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4D1D2297-0497-4624-B685-86B9830A3105 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B8DBEDD6-3979-4BE4-8D7A-34CA1232A4B1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 96E29708-BE6D-41C7-81DB-2EEA73579BE3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F9C10356-C61A-44CB-9E7F-C8E2176316DD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 783CD4C6-BACE-485E-8121-2D07EC9ABD4F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0790BF1B-0E5B-4AAC-9B48-2C2FB4A9E13C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5B7D56C1-F670-4342-97EA-2DE4CAD9E9E0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2B51AC72-8A5A-4DB8-8DCB-CFD4D5E7F695 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 56968308-8388-4847-95FA-2D0221556F3A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EA90CF61-D43B-4120-997A-E60E5C25C54A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F8B176AC-50E0-4EB6-A451-E012EEAA96E7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FE917617-7A9A-46D4-A3AF-92859ECDDAF8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 02D0F9AE-1A5F-4C51-BCE6-AAC9097FDC83 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 27B1EA98-214C-4EFE-A2B9-CBBC6937A06F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A617BC79-1827-4B3B-9D97-E53D32F3A39A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4BFF7B22-6E25-4B4D-A29A-ADC937F53C03 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 32E0A9F0-2847-4BCB-BC02-D317454FEA9E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 53EA013D-D3E3-4081-823E-2E8BF8D88AD7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5EA32158-0172-4A2E-B239-19FC66C01A57 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7F53ABE8-6278-4417-922D-1E4780E62A76 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 537C2CFA-3ADA-4D78-B492-C4BDDCC13448 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F155B182-CA08-45C5-8E38-FE4EF6B89787 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 622F4989-E66E-4006-95C0-467AA62E3A4A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 27732B04-BB0A-4B7E-84FF-3CA889077ADD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3C384F5D-AA87-48B1-A94B-FF8115D4307E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D7BB3D27-5DB4-49BA-9A77-0EBB2416EE65 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3E71DCBB-5459-4ABB-A5E4-6B7AC9F18BA9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 00A378B4-440F-430F-9F66-0640227DEA4D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 96384BF3-7881-44FA-9BB8-8F6A4BB9D347 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 40CC5AD3-3325-49C8-BB57-F6BABCC2A614 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D141827C-9CFE-46E0-A0FB-4325BF602D64 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3A79C58E-3C74-4A57-B106-155C50B4BC1D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A509A3DF-840F-4F2B-92F5-450B80E0686A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9CE8A729-7742-4DFC-A279-34BB7935AC0F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1B379235-4269-4231-80A5-ED8E469A3344 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3177D876-CFB7-4B15-A816-D850830B0F65 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8E529A05-BFAC-4E42-81F5-3AF5B0B79CC2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2D778B55-0404-4214-AE75-11596F1E570F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 89865C72-8194-4894-84DF-2E5C6D986B89 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 512A7C90-E356-418E-8CC8-4A793439FCF7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A38C5991-B722-4CCA-BF06-FD879B801CFB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 769F8865-1C5F-4C02-A93E-EF6F93BDF526 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 35E1B3E6-3215-4AF4-B6E2-63B46D97B1A8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C11AB78F-A86C-4C49-A7F6-24556F871424 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8ED03CDC-C3FA-45CF-97BE-C2C6FC0AF519 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B47F3D0C-EE30-4AC4-86D7-95A511BF7C02 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 812C2F2D-4693-4145-93C2-02373F6916EB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8EDE869D-2587-48B5-80CF-5DEDAE1340C5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E7D9C9C1-93F0-45D8-8E8E-4A4C862AAA51 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9C25BA17-134B-45F3-9D35-1289C77172E6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B41EBA57-FEA3-45DD-9E4D-09EBD5294F6E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 55802E65-5546-4673-84D7-06283A82AB8C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D030B4C0-0C7E-4C4D-9D8B-25E138C8DBAE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 02C52F4C-A5B5-4471-995E-112C21BE4B5B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FE7FCCA6-82AF-4829-B8C3-CDAEE36A957A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A17BD06E-8649-4614-AE62-AF764A4E75FA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7EEE6F22-5F7B-4F82-A994-654F22742CF8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CA61347B-7AE7-4272-BB76-2112F7F26AC4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A5891F0D-422F-4D6F-951A-60B3BF333BDE --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-06-01 '-XMP-ph:RideName=Cânions da Brasilandia' -XMP-ph:RideDate=2025-06-01 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=S 4 — Cânions da Brasilandia' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=S 4' '-XMP-dc:Subject+=S 4' '-XMP-ph:RideCodes+=S 4' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 39 — 73 foto(s) ===
DEST='/Users/danlessa/pedais/2025-06-03 - PH 39 - Água Espraiada da Foz à Nascente'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 799E1E9E-C401-44BD-991B-08150AE036F4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 47929E52-5CF5-40CB-859C-E9319F95012E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AF6A926E-644E-49AF-BC3F-A16181077886 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D3B12BA5-DC10-4216-98EB-81D0EB7B4925 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AF61240E-0A17-4538-AF7A-7F3ABC2C65B3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 099A2A79-0203-4530-BBE3-8A0E934F210A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F2C7E121-14BB-4C6C-A965-9A6C37B21A25 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0EA68700-C47B-4071-99DF-695FCBED73EF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B563C9E9-0293-4AA7-A9A0-D9A87B26309A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 67814D50-507D-4064-9F5C-EA6E0C9BE2DB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 54FE72AB-2ADA-4340-A493-8594B4471C4A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D35239DB-9BEA-4E5D-9553-083E9D4D3582 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 254B0FD6-DF9D-4ED6-AFE7-282D3E1DBC01 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 41A847C0-EC96-4392-9446-D44418C57DF8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D16E0DBC-3F92-4FC2-A7C0-8A2EF7F902D7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 52EA0DF7-AB5C-479B-B83F-631FEA8D5958 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 707564F4-349B-45AC-9D25-DA162B11580E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DF20C911-AD2D-4006-89B2-F2037D461743 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 223AB331-42BF-4722-9294-E3200C2117A9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D98AF3EB-3D9C-4E25-9CEE-F833F5503E9F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 44857EC4-306D-4D95-9706-8FEA3DEA4F6E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 24C43CCD-BEEF-4F02-912A-896E746BE9A8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ACC436E3-5113-4BC5-B1EB-CA3A04E5AC43 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4FF9A90C-E9AA-4E3B-9B05-3D3F5C3F20A9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2E3EED9E-EC71-4B31-9042-A5ED6E41B8DA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0E93AC43-37AE-4A53-B9EA-F1C39CA61644 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A0EB8EE1-3E98-4FEE-8513-9026A35DB2B3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 62FF9DBD-EE82-4157-AD2E-449C9702725B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DD94CCAB-F4DF-4A6A-A688-29CEDF562713 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A1B4E387-71FC-4380-83DC-6BB4F613EB78 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D515661C-786E-4D48-A550-2E6D69E410A4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5CA3FB9F-2925-40A4-9F76-D54140F9D9C8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5B07AE5C-BF18-43E7-8D45-DFA3E0B62916 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D6415FC7-267F-449D-876D-7EF4EECE5C12 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 001960E4-2D34-4878-BE23-6287004D1C4E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2BD85D16-72DD-44BC-9926-0EFD64F9CCC4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 914538E0-981D-4A15-B67F-7E47E7AE66A8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E8AB7D47-7644-4D2B-9D41-6E2FA266CB0E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1ABE43FB-8045-4DB7-B673-5235C4542AF5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CD1EE9D6-4551-467D-A37F-37EC38C32035 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E7B558FF-F93D-43BE-9338-F52B314AC0AB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7AAFA76A-77C3-49F8-BB13-2F8360FA77A1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B67E58F3-21D1-4F6E-AC47-717032901CF7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7FF43421-D70E-497F-B980-CF1D056833DC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2C1ED216-1B01-4528-A994-C39AEFF293D7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 14E66C1C-D3CE-4931-BFCF-357209FCEBF3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A6310AC8-8465-4129-8573-6F41E19B2677 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4990742C-9CE8-4519-868D-12756269A96E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5AF6A8B3-9C90-4BD8-8B8D-9408E6EB77AD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C66FB82C-58D3-420D-B1CE-B9C899A52FEB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6D6DDD61-C13D-436B-9B57-5AB884E9F64F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CB1322B4-01D0-42F2-8618-3D634F427D62 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 68551351-AABF-4E24-AC73-8C486A532CA6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B72B5E11-65CC-4233-9BAD-BF8168ED906F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7B86351B-FAE7-43CF-9F94-2E26FAC3E14F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C249DECA-7250-4FC6-A81B-B140C832FD1C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D8ABE373-36FD-456E-BE21-39C73B14AABF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 48350D75-87CB-4919-8EC6-6D52699C84CC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7BC79909-4292-433F-BB5B-8C15D5C87D3D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6ADF6394-18BF-47C4-BB69-93C42DA0B1D6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 20C31CC4-C32E-45DF-BD73-6CB3017EBDA0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 27CF68BB-FFDF-4C25-800A-295B99B32948 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D70EFFE5-7759-4624-A3C7-5972E610E39D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4FB938E4-C6CD-49D7-97F0-7C6B4F12F29A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 352FCFC2-956F-4399-B63F-4CD8F7DF2FD3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 89E0A56B-89D3-48E5-BB71-58E36DAD0BD9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3A3BD2F1-1671-4D69-8437-4A561972F430 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6B18B75C-2FCD-4478-B958-5B2FF55F245A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 45056776-39AC-490D-A107-BB2FB5156A0F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2E23C96C-096D-4836-80DB-1DA4F377ECB1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D4A325C8-E941-4C03-B64B-9EA568DBFE67 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CF211196-0160-4A25-9132-EC40EB21F6B0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 93161465-CCC9-4DDF-9D27-85058353A58D --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-06-03 '-XMP-ph:RideName=Água Espraiada da Foz à Nascente' -XMP-ph:RideDate=2025-06-03 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 39 — Água Espraiada da Foz à Nascente' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 39' '-XMP-dc:Subject+=PH 39' '-XMP-ph:RideCodes+=PH 39' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 40 — 75 foto(s) ===
DEST='/Users/danlessa/pedais/2025-06-10 - PH 40 - Crista da Mooca e Médio-Alto Oratório'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 22017B9F-7A23-44D1-91F2-B03443B0C148 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AA4E9AE0-CF58-4ACF-B67A-4B5CF1B5D914 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 40601128-D3A5-445B-9264-578EF61687D6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B4F196CC-D9FE-48E4-8BB3-8E03FC6E2BB5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C5541755-9799-4D99-A3EB-31E7E5B2BD57 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D45B428D-9460-40E8-B71F-DD32BA231237 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ECB67A2B-E77B-469B-AD67-F986EC13E7CB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DF97EB7D-937F-4183-AA2D-6FC48D3FF95E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7691B2B8-BB0D-4935-8598-1472B889916D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A8D9A71E-B9E2-4AF7-AAF4-F68FB011D9C1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 70EE1D37-7A75-47BC-8D3E-54BC462AA0ED --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3591D178-A5A6-4256-BE1B-923F9C43B94B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7004614C-BF4F-44AB-B8CE-3DDB717176AA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8524ADC0-742D-4657-8168-0E4B20E728E2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7260EDBA-BC7D-447B-919F-38EB6BD9640A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EE49D1C7-4C00-44E0-B52B-1E4072495F99 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5DF36A9F-39BC-4BF7-A88F-2407BE4FE060 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 40D30BE6-991A-4F70-9E6E-8B0FBCDA94D5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2978CE48-30F4-4B84-82B9-0FD7AA1D71FF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9454FE0A-670E-4BE5-BD91-458FA1B76F1C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EDA54307-9803-4D2F-AA27-AA9443DD38B1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E382A0BF-495A-479D-9A16-541019FA6831 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A7A91BFC-9B5D-4533-B21C-EB99990EB4FD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D9A1A5B5-D625-4D37-9995-CBE0C322D410 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 26746F74-CB4F-423F-B2F2-B18567D685B0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7D4B49A1-DF2C-459A-8026-7AED6F42876C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 49BECDEA-26A3-40CA-99CD-6C19C7951854 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E7B2BEA2-BF63-43E9-B689-5A5930A78B00 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 582E846B-3AA5-4C6D-B5DA-B4AB8361805D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 220B5C36-21BF-46B8-8DEF-95780AEF313C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6968C410-647E-4152-AD8D-41B2ACCF83A8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 115D0B64-E312-4408-B8C3-4BC23CCE3E7D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9FA4464F-91AC-4054-BBD1-29E5D7A07194 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BD8C77C4-A8BD-448F-A4EB-B7C6632D3D35 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 439D94A2-202A-4E12-A8E8-18ACB8DA27F5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 544C565F-843A-4EC4-8155-5B95C4856C87 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E5883C48-AE11-41A6-8A61-C91601E7259F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 14EA3337-B79D-46C7-91A0-7DA0D7125796 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E63D3D92-A469-4E65-A10C-8F6F5F3B2398 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8DC4110A-7FA6-45BF-8D47-803F72627E07 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3AE7A1DD-DCED-438C-8988-438F1748CEC7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CC2DB900-B34B-4260-8021-8E77C24606BF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 38BAB166-8540-4B37-8A2F-CE3D1323E78E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D7D50B4E-1423-4D8D-9D99-934425659AE4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E50761EB-20FA-45B7-B8AC-82541559A35C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E5634CF5-58DD-42DF-8FC3-A7DE3C659C89 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 36294BCB-820A-4DCA-B24E-B0D244AC6F40 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 06D0DA76-61C8-48DF-A044-7A82F1E72CB7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E53E00AC-A92E-4C16-B85A-79DF66BFE425 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0954251B-75AA-40FE-8ABC-E343F319D0BB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4BF9755C-7C72-4BB3-A18C-658A57A0DE29 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FD8EA068-B253-4012-8F1D-FBEB8ACD35B8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A5F29E9B-48C6-4949-8240-1213EB3E54F6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3D895503-F332-4FFB-BCCC-9C6E7E4633B5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E43E3E24-1EE7-483C-906C-892A39489A99 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F518B667-EDBF-4115-A426-8E6068BA6407 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 29D5823A-1B73-4AAF-91C5-02B33D51BA1A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 82A02DF6-ADC6-4491-B6B8-3000008C0406 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1AD22EF4-6702-4F97-80B8-A1FB3F71DC97 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A00320E9-2966-475D-BA77-F2839E67852F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0D7EDB1B-8390-40E5-A415-875B0FEBAD9B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BD3E72CA-A0DA-4228-B52B-C1B1224E3C9D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A184E29C-EC5F-42F7-A68F-BD9097635F43 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C4FFDF57-C5D1-48C6-B2B3-999CED15C0DE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 64D06EA6-E2D2-4E63-A279-C260437E4FA6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1923A37A-6904-43ED-9A28-C08A2147C092 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ECD7A1CB-6EC1-4623-9358-BFA7A7C8363C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 94CDD950-28E1-4365-862B-EFDB605DCFC2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 03B7D35A-52FD-49FA-9497-F370B8C6E672 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9F01D8E8-A127-4E0C-9DE7-79EDDF48981E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C6A03FE9-CA15-46E0-8B0B-C0A2A5DDC092 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C3B4D891-4C81-469C-87CE-2DDAC62396F0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F9E0D4CB-6E0D-422B-B50E-76FB84EDB40C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D2B3F81F-AE84-46A6-90C1-9B5D200DE563 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9B8D84F6-21DB-49DE-9D14-9B05C8CCC423 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-06-10 '-XMP-ph:RideName=Crista da Mooca e Médio-Alto Oratório' -XMP-ph:RideDate=2025-06-10 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 40 — Crista da Mooca e Médio-Alto Oratório' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 40' '-XMP-dc:Subject+=PH 40' '-XMP-ph:RideCodes+=PH 40' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 42 — 74 foto(s) ===
DEST='/Users/danlessa/pedais/2025-06-24 - PH 42 - Carapicuíba duma nascente à foz, vindo do espigão da usp e alto jagua'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 963A0670-0F60-4668-AF79-6EE476A41F77 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 035C0B0D-C111-49A0-8AD4-6A9204A8DAD4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F5B3C89C-488A-46E4-940B-CF08358E3AEE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 26A19DFB-63CD-40EE-A03D-2DE9B2D551DB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AF77DF21-30C2-4E52-9FB8-3E9E1167102C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D1BDFC43-13B0-458F-93C3-46767267601F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F6FDFE1E-7FA7-4AD1-B72E-3D1B3C2AEA4E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 733B3A0D-065D-44A3-B614-260D178C9E7D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 75BD7C66-3073-4DAB-BD55-5EFD28F28883 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E27588EA-6651-481D-948E-ECFBBE62E15F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F24BB3B7-C02F-42D2-87B0-9C7DB9D7C403 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5B558CAA-8A84-4651-81D0-A54E34D893CE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C550B720-A879-40DB-865C-33034E6ABD52 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5BAE59E1-0B78-4F17-A422-0F91233C1253 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F2156F64-E9BF-4B7D-86EA-69A6262AB76E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 56DC59C9-5CC4-4FFF-94F1-AFE957C111EA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 267EBBC6-4B74-4A22-A4F4-88C63D28B218 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 89E4C136-8451-4466-B136-F034CCB6BAE8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 42135207-05CC-4F3C-A1FD-95AD36EBB495 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C996D064-33F1-46D9-81AC-9D2D98A121FC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CEF78B01-78AF-49BD-B303-110504FF0FDF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F96C6D8B-94FF-478B-B0A6-44F51E79310E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9E57871B-442B-475E-9C2B-41BE317666C7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 85124720-9115-4E4A-8772-6BB7F3CC426A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B83259F7-11D1-465C-A5D1-3AC8D635726C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C614BA1A-8AF5-43A4-8FFF-63511E120A27 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 78B5FDEE-0FC5-463B-96D6-1483C7806D4D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F7A03821-9C3A-4F71-897C-DA55D0D58826 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2472A945-ACAC-4FC1-96AE-9E32AA917B9E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F0FD1FFE-B7CD-4299-AAA8-CD6526202B54 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8728CE4B-C99D-4AB4-B9E2-CBFC3F66FA03 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 32CCA4EE-3DEA-4737-8DB6-6127AB66EB21 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 80A3EDEE-036A-4BD8-B408-9204241D802D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2773468E-47FA-48CD-BA68-3A2F53059854 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 28CCD00E-845B-4AFE-90AC-DBA662B83267 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FA8E6987-9B3E-46C1-BBE8-E11FA35563A0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9E59CE0D-0792-4948-AADE-C5C872771C85 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 968D83AE-A066-4BE8-96D2-8920E45B8A49 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B6312027-291B-4D6B-9B4E-9E243A7266D4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BFCC7257-579D-4826-97AF-A69BE96544D9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 19E851CD-44AF-4C64-8B2B-1F2922495FD2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5A3A0D3D-F0A5-4B3A-823F-4CE7A5E971A0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EBBF5277-3B84-4A62-B773-7E8FD76C9210 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 58F5EEE3-EDD9-4685-BBCC-054993054ECB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7CE5B1A3-A964-4444-9003-6FB478711A65 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E2017CD1-303C-495F-B688-E9F42F79E487 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8F191B3A-4D37-4813-9FF2-1AFC5D2BAEAE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1DC617E3-C0BF-460B-9D44-7DD526391F38 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E338CEA1-F9BE-48E5-A12A-FFB5D22CF5B8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ECF9CD8E-9052-49AE-9A70-6851691BCAC2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 332010EF-8523-4AFA-BD1D-89A25F130638 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 177E0037-1BA6-41CD-8539-D3A16AA0484C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3D8BB705-8523-4015-9F68-7193C8B25C7A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FEB47154-4E3E-4EBB-8E3E-3928393F9112 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 268E1A84-E0DA-462C-82F0-143950F4BA7C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D286E1D7-09E9-4104-BAEA-5ACD58D3DF01 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3EB45A7A-0DF0-4ACE-90F9-459C826709E2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8152AD69-2BD0-41C9-9AF1-F9FF8E511E00 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 153CFB4A-64CA-425F-BDEF-83B887A7AC8C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1CF8B323-9115-4110-9261-6267F3D8B3DF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 918368ED-3E7A-4FE0-BE1B-103F0D6857A2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B0FD462E-A5F2-41B7-8363-65C77D5F14BE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4D7D3B9B-69AF-4110-BF6A-C6C38D7EAECA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 10FA9AFB-B57A-4EA8-BBA9-05CFB7F48C32 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 90083930-E183-420C-8ABB-350C06C042F8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 858A2A71-901E-4506-8A06-003D81ADFF83 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3C8D63A0-DADB-4570-92A2-6371CAA0181C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 224A9C8F-63CF-4FB4-B6F6-9155D50EB338 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D580E93A-B3A0-4725-AF2F-10119AC33356 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D5EA3906-D7D2-4950-9FFB-E8C2EA2896FF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2841BF0B-9FEA-48C1-8202-AB96D90AF1FA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BCAE69D9-55E0-48EF-A8CF-93F9075433B4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FE025A6A-FF72-4149-ADB0-84FD18BABB41 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BE21AB7A-EA06-422F-97B0-4B221EEA8A07 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-06-24 '-XMP-ph:RideName=Carapicuíba duma nascente à foz, vindo do espigão da usp e alto jaguaré' -XMP-ph:RideDate=2025-06-24 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 42 — Carapicuíba duma nascente à foz, vindo do espigão da usp e alto jaguaré' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 42' '-XMP-dc:Subject+=PH 42' '-XMP-ph:RideCodes+=PH 42' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 43 — 56 foto(s) ===
DEST='/Users/danlessa/pedais/2025-07-01 - PH 43 - Riacho do Divisor ao Baquivu-guaçu pelos sopés da Serra do Bananal'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 38D152CB-89DC-4E92-8D17-A5462C242EF6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 79913CE1-34B3-43CC-B26B-D4EC94E2BB00 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B0883378-020D-4D54-89CD-2F226C756E7C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 94BE9E6F-42DB-4704-B354-0D58CFFBEC41 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 88BA8D71-9A87-4ADF-A89C-295EA05A9E04 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CE073806-7F6E-46AB-9626-29608BB688E8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D8B68436-4876-4ED0-BB42-CA1C4023F228 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C04EB32A-7675-4B73-BE4F-2FC599575A37 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D0DC9419-F5D4-42C7-A6BB-E6595F579AE5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6C0DCFCE-5532-4905-A856-C0D094CA1C2C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F301C087-3016-40DD-A0C9-012E88057BDA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 93584E5A-79FA-4CA5-9958-F806574D8247 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FE61BF35-E298-4A54-8202-F157C82CABCB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7CA87BC9-5414-445E-BFE3-65D35EF22BEB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6ECDA3B5-AB7B-4DE9-84A9-F9DAAD61A3B8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F0B47B4B-EDB7-43F0-8328-C21D542FC663 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6E9315A9-1536-42DB-B9AF-2241E1F2AACE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D71DD039-73B5-4F3F-BCC4-90FBE9883D5A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F076D027-E5A6-4C5D-B065-0162BFE207A4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B63656C6-EABB-43F6-99F1-071E5A43C511 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DC6E0359-B735-48B3-B61C-F1B963482DEC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1FEA56E8-0009-4DA3-9C88-F2BA94140C7C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4AFCADDC-8354-452A-ABEC-8A43B0A25E6E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 98D33BA6-5A99-4264-B1B9-DC3213E4DDC8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2120B752-23D9-46F7-BEF3-24A69F984929 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 751F97B3-44BD-440D-B443-AAC64639B816 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7CB51365-7B58-44E8-9324-0D5B45E7FD71 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D807A7C6-F98C-4F98-9708-A993C8B7A8DD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 934F75FB-678B-423D-B575-A305CE00FF60 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0DA4CEC0-1A04-4A50-B2C6-AE5E01E1C55C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C1ED13F5-5C79-4E82-93E1-14FD34089812 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 08801FD8-8F9D-40A2-AA60-7E8B9AABB66A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A2965BA7-9FC2-4048-8A1E-785EF6BB062D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9AAA4188-2496-42B5-953A-6702975FD33E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C439E634-50BB-4512-A693-9B1BE7CE9768 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 21E30405-61CC-4A17-84F6-1A441A735439 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 28C34422-EC9E-40AF-B054-5E12E86D8C59 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 90FC4767-9E01-4952-A24A-47B9156CAEA0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9951F9F1-BDCD-4210-B11D-3F2EE9805398 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 40BA14E8-911F-4971-AA55-4AE3F62DBB2D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 79822034-616A-4BBA-B710-4C790B6E8993 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BF3555AB-692C-4463-8CCB-499F24040B3F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0DBCF5FB-3236-45BF-BBAC-16C8538C4FE5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A92BCFBF-38CD-422B-A334-6123FB7AF988 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 152B9BCF-1EC4-4FF2-A8A9-8099D1E2C71A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F24FDE13-AB06-47BF-B39D-FAEC79480A09 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C5D6873B-D0B3-4EB3-8718-7BFBA7EE5F34 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CED5795E-33A1-4CFC-BCB5-8809682D285E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 58C20F93-B196-44CC-A47F-70B0BD31D2A2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D178F037-C32E-4696-A45C-600AEE1F0FC8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8792D77E-B0E1-4FE9-A369-30F6DBD8F4BA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E625D14F-99E4-4B23-BA8D-A443EF0EB0A3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7D7E46B6-787C-4A6F-96D2-C22E554DD4C7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 05A87053-1336-454F-8474-22C104917AEE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1EFEA0EC-7F9C-4846-8369-71BD04D4F00C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 280FC8D8-F24F-40B1-805D-B12A44E8A2E1 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-07-01 '-XMP-ph:RideName=Riacho do Divisor ao Baquivu-guaçu pelos sopés da Serra do Bananal' -XMP-ph:RideDate=2025-07-01 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 43 — Riacho do Divisor ao Baquivu-guaçu pelos sopés da Serra do Bananal' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 43' '-XMP-dc:Subject+=PH 43' '-XMP-ph:RideCodes+=PH 43' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 44 — 51 foto(s) ===
DEST='/Users/danlessa/pedais/2025-07-08 - PH 44 - Foz dos Meninos à Foz do Zavuvus pelo Riacho do Taboão e o desmorrodo'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 3E0F74A9-DF8C-4745-B058-454879390EF3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E4340BB9-DF48-4887-8A27-4F0CBCC95B9F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 484FE5EC-5D5D-42B9-92FD-0BB614CCB322 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C536970D-988F-49EF-AA4E-079121502B26 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2F668F2D-D00A-40C2-968D-96AA61CB793A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D6CAA20A-50FD-481A-B6F6-ED71509A958F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 86273602-B7E8-405B-AD14-9AAC09750EB4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A027DF60-5182-4315-9C80-3816B308AAA7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 84E6C7BC-CCC9-434E-B84B-8E0C8712E0F6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E97C0AC3-FF65-4316-9ABA-0F7C2339EEDD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 24099E57-9F0A-4BA0-A2DE-1D3530A7CFBE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 81D7E809-FD69-4F60-A0D0-61AB3DD5B7AA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B2CDA286-DC4A-42B5-9CDB-8ACB07943E09 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 13830AFE-9D51-490E-AE51-BF5A3A66920A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C0A3715A-8F1C-4B23-825F-571113B6566B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 459AD1E0-CF36-4D4B-BBF8-6C2E230241B7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AEEAD3EE-361C-4096-A091-CD39AF8460B4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 018EE78E-FC2D-4F1D-AE34-2A492555C099 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0D595EA1-1E32-4512-B9CB-7AF5CA353AAC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2019C844-4005-4A47-A499-FC7606618DC4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9E5D59E5-18D3-4700-A2E2-EE6E17E31041 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CA9A6AFF-0AC0-4D1B-BE0A-3F19B5B3EFF1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 34EF2763-D77B-4F7D-8B25-91DC80C7A9B2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 709F2943-3721-4D2F-88F2-BB45E1ADF664 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 065EEF92-B75E-4C38-8069-AA2D9847E028 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 49C85158-B6F8-4462-817B-CE59C940209F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 81D58B3B-1875-49D0-A386-360D63964F11 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EEEEF0D7-AD95-4271-846E-D0205C40AB3E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 68A5E4D2-A0A5-4BB0-A14A-7EE849837598 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D9E99934-D9BA-4C1B-8E85-7F9B0FDEE6A4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CCA288DA-4579-47AE-BD3A-0B100D95A899 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D172B5CB-17E2-4EDA-A754-2D11B882EBE8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7015F9E5-954E-4325-A268-AF9F95299EEC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7B08BF1F-5D54-4A58-96E6-86419734BCAF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6A032CB8-A065-4DFF-90D7-06664755BA2C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 372D6A57-0019-4F51-8080-2853B651D8DB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7C386683-FB09-4A03-B9B0-38493AB16DEB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 66ED980E-0273-402A-9AE2-F5F5219584AB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A2208641-F047-4477-93E5-DBF1563D0B7B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C2E97A2A-E3E5-4155-B890-768F1BD7CBBE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C3E8106D-04A9-4EB6-9B66-941166CB879B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B4EA7BA6-653F-4CC5-ABAD-F7671F4DFBCD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1983ED56-F6BA-467B-A8AF-EDF891CA30B1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B9CE4037-B6E1-4A7E-9838-5258258E0BA3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 535EBF10-BED7-4C69-A426-DD52E463124A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A92811B0-B557-4724-8413-80C9A6DBFB0A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 25A47978-EA59-4B7C-9068-6FCA57F72B04 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7B0B7359-FD55-430F-9C45-1B6CF790A33C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 434F73BD-66BB-482C-B5AB-7E2B927BAC60 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5C5DFE5D-2E83-4B32-A25A-4A69A7EAF045 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5569111F-CB94-4365-8BF6-D5F1E5C7B571 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-07-08 '-XMP-ph:RideName=Foz dos Meninos à Foz do Zavuvus pelo Riacho do Taboão e o desmorrodouro do Caaguaçu' -XMP-ph:RideDate=2025-07-08 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 44 — Foz dos Meninos à Foz do Zavuvus pelo Riacho do Taboão e o desmorrodouro do Caaguaçu' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 44' '-XMP-dc:Subject+=PH 44' '-XMP-ph:RideCodes+=PH 44' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 45 — 51 foto(s) ===
DEST='/Users/danlessa/pedais/2025-07-15 - PH 45 - Pirajuçara da Foz à Nascente e Cabeçeiras do rio do Morro do S'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 055020A8-2E17-4A3E-89C7-0834CEFB19FF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BBC01C46-A3DB-4328-B2D2-C5BDCE89F044 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8FD01AC8-E909-4C05-9668-70472E7106B5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4ABD393E-D9B4-4A41-96D1-EB0686712147 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 39955735-F9AB-4FA5-9209-097BB56E4EBF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ED7F2800-ADC9-4356-ABDA-E8BB67A9A3DC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 163C81FB-2CFE-46BC-9D0F-B17BF62836C6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 580037BC-7C8F-4D4D-8E7D-CF14B4F2A3CD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 92D8E956-3050-4A1C-974C-F2443544A6E9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D3444115-712F-48DD-AB04-5BD4E9A35911 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 836F191F-BB83-46CF-95A6-FAC333BD57FE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 85A31538-740C-4D0F-8E69-B2AC1E81A1D0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1D09A466-D8E8-4790-AE1C-B5D9F01C2FC8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E9D0D622-4824-45B7-BB51-DD250CD94EDF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5AB9289B-5BC4-4AA1-AE6A-25BA3F8D3DAB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 99A7BCC2-29FD-488E-AE06-5F5580075F2D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CF0B004E-58BD-4FAB-A735-7B43D0905FE4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 62E2A822-4A4C-4750-A364-869F4C8202AC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8EC22DF0-3682-42B2-9321-FA291E16EBA1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4E8312F1-C1A8-4DEC-9EB8-79C670112134 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F5493CF4-DB20-4129-9D1F-F9302841F442 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1C759A58-1E9D-4CA8-ACC7-461B302DB764 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3DA0F709-3687-44A8-B22A-562C678D3AC5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 457F9E3D-0F32-4BD1-A205-F126C2A55296 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 43811F0A-BFEE-4047-B47E-B97692B0B309 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 49D42C87-B26D-44C0-93B5-505AA1FE8C8C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 60EAA4A6-EE7B-4319-B6D9-073C4885FFA1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 408B8E1E-478B-4FEE-AAA8-EBAF1CD763CB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6F8CF257-CCAB-4915-8A51-3893C69F0C2E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3A8985C2-4806-4F91-ADFB-6FB16D6BED4B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B2C3772C-780D-4C6E-AFC7-6336B9D30339 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2D1F0960-D56C-4368-9EF2-7780839D11C6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D6F9A515-3289-44AB-9134-6D305624E187 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F1C97803-8640-4071-B60F-C46C1BD1F7F0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 92347388-423B-4EA2-80DA-C08AD5677B3A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6CFD6EDB-A914-462A-99B3-399058EBF6E2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 64909750-8FBE-40DE-B432-A01355B1635C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BA8238B2-135C-4B83-BB45-7FDE7B32261F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D9082703-6760-4CA3-9A1F-DADE6BCC20CA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8B22C24A-EA25-4687-AEF9-937D5E531E1B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1E1D21AC-942E-4569-B021-0E9E28FDED65 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F9BF5C29-C4B5-4B49-AA14-5F9C3841580C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 97962EC7-BD9A-4341-B949-428682AF0E40 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9505F366-7D51-4E86-ACEB-42C03E69C461 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AAAB6AE8-CC65-4B88-BCA4-22780D1574DE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3D9C4D52-F9B1-460A-AC75-B6D484DF422A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9DD80CFE-117E-46A4-AD1A-CC322129A6D6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 817BFD17-5CCF-47F6-8206-88539FFF2D52 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DE1709A0-389B-4B63-8435-998651144462 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7C3236D5-C71A-4B79-B22F-5A85289FA72B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 168C04EA-AE13-4945-B734-8453160C6D9B --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-07-15 '-XMP-ph:RideName=Pirajuçara da Foz à Nascente e Cabeçeiras do rio do Morro do S' -XMP-ph:RideDate=2025-07-15 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 45 — Pirajuçara da Foz à Nascente e Cabeçeiras do rio do Morro do S' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 45' '-XMP-dc:Subject+=PH 45' '-XMP-ph:RideCodes+=PH 45' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 46 — 29 foto(s) ===
DEST='/Users/danlessa/pedais/2025-07-22 - PH 46 - Contorno Central da Enchente de 1929 e pizza no brás'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid C89BC038-16C4-43C8-9EDC-0EF7B931ADF1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 033699C8-3B33-4DEA-AA98-9D8B2B565599 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C84134FF-376D-46A7-BECB-5EFB938C3953 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A2245514-2852-4464-87C4-B8985A878FF3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FE3EBC6A-E451-41C0-A57E-9D49A296B80B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 94D8A5B3-25EE-4A66-A76C-366CECA6C328 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8AA02162-DEED-4554-A6F9-A03188DEEC2E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 015BB93F-9DBB-4160-B526-B8C0CBB20903 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B5241F48-6DD9-4530-ABFA-4759FB918941 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C7E01F84-7D42-4A36-BDEC-723E2E42935A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C6ACBFAE-F80F-4CD2-AE81-4F1EEFEFE6C0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1314042F-8887-4B7D-BF0F-9AE93346048B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6DABB86A-EEC3-48B4-B0A6-554EBBFBE263 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E1CF0DA3-EAB4-4353-814F-BF3F981A48D7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B02DCE48-59C5-4B41-92E6-46DE493AA379 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 61E5FB13-1FB4-47C9-BF09-AB02F740F965 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C42EE8BD-8747-4B4B-82EB-9B8E6D980D38 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5C2222D3-4EC2-4935-87E8-6E2D369EABF2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6AC9CC2A-2147-4ACC-AA64-1D0C33229F73 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 57CCC517-EA97-4F2D-A907-82A1A59A7372 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AD0F649A-5AB2-4D54-A877-3CFBA6CF483C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EF3BC75F-4282-4561-9757-0CE2927B715D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BD3A7BE7-3707-4C22-8D71-A0AB2D00F7F5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 90BB8C31-05A4-4237-A8FB-AFD711B2F9B9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C6A89038-EA87-4EC8-A3FB-0C3156EFA035 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7FBF94DD-2D7D-4E76-8D0F-72A1B2F61AE3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 00720E1D-CCAF-4C72-8D71-A8AEE2EA6D8D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3B96E093-3A74-40CB-9855-9BE23CB61A63 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 850D5599-AF28-48A8-8B28-CB8ECD5E5C39 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-07-22 '-XMP-ph:RideName=Contorno Central da Enchente de 1929 e pizza no brás' -XMP-ph:RideDate=2025-07-22 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 46 — Contorno Central da Enchente de 1929 e pizza no brás' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 46' '-XMP-dc:Subject+=PH 46' '-XMP-ph:RideCodes+=PH 46' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 47 — 5 foto(s) ===
DEST='/Users/danlessa/pedais/2025-07-29 - PH 47 - Margens destras do Jaguaré, mirante da década de 40 e pastel de Oz'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 962EC385-8E6C-4620-BE03-ED9E31C8E989 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6914147B-AF2D-466F-BBF1-25FD8338C3AE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EAAFDD35-0F46-4729-B8BD-578392647115 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4ECC40E1-F5C8-45AD-8D60-A0FAB35FAC52 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E01D0C9F-13D4-41F8-B8A0-7B27C42C6C67 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-07-29 '-XMP-ph:RideName=Margens destras do Jaguaré, mirante da década de 40 e pastel de Oz' -XMP-ph:RideDate=2025-07-29 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 47 — Margens destras do Jaguaré, mirante da década de 40 e pastel de Oz' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 47' '-XMP-dc:Subject+=PH 47' '-XMP-ph:RideCodes+=PH 47' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 48 — 6 foto(s) ===
DEST='/Users/danlessa/pedais/2025-08-03 - PH 48 - Sopés da Cantareira- Tremembé, Linha Verde e Piqueri'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 4B9A9B0D-5902-414C-B777-95B8EEC47D7C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EC3EA533-9449-4E1F-A6D9-965FB0BC71E9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1996606F-930A-4D04-8338-063FDC1810D2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 509C3343-B0C8-46B8-A462-3C21CBD4FC7E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4F6F2D49-055C-40BC-AE53-493AA7AAE08C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C88F5780-1BD9-4BD6-A4C3-4A632BDF7269 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-08-03 '-XMP-ph:RideName=Sopés da Cantareira: Tremembé, Linha Verde e Piqueri' -XMP-ph:RideDate=2025-08-03 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 48 — Sopés da Cantareira: Tremembé, Linha Verde e Piqueri' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 48' '-XMP-dc:Subject+=PH 48' '-XMP-ph:RideCodes+=PH 48' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === Pontos de Sela da Média Leste — 45 foto(s) ===
DEST='/Users/danlessa/pedais/2025-08-05 - Pontos de Sela da Média Leste'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 3C3174EF-0609-4A88-8539-D9683BDDC526 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1FFC9159-1B88-42C9-BD34-053550990791 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 526056FE-641A-4B1B-86BF-2D11AC0C2562 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B7D81603-598A-44F9-9017-744A878D07DD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0060B2A4-4232-496E-B95D-51C525905687 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A85B6B6A-32CB-4F31-816F-DAA49156D403 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D342F620-1050-4188-8DEB-414BA8DE438C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B25A4083-0271-4D71-A72E-6FAD965C8143 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7FAF2CC4-B0E1-485F-9F71-5D48F322CE5C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F479EFD5-0563-4ADE-86AB-0D202951742B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 85D4BE91-6181-459B-B25C-2DC9B4D00CCE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B4E448A6-9FF5-4B2F-99E4-92D620F5DACB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0270C7A3-0637-45C3-8BD4-F1D5701B9F08 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7A617498-C523-4220-AECD-92C9BC4CE73F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 248E4144-4FF6-492E-93BC-7206486F5DE2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7F715DDB-0F89-473E-9FED-5C496D87B7D4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BFE00CB5-498C-4BBE-9A44-0E00E69A7EDD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 03F75B46-95FC-411F-8E61-C67E3A6B9CB0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 24E5E1E2-5B2F-4250-97A7-8CC50942B524 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 91A99B5D-B8E0-4499-A922-E69730EAFC8A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 08074846-F072-4CB2-812C-3DF651BE7ACE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9121E434-5FF0-4A8F-83A2-1D3EBB326B15 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9FE9B87D-12E6-4352-8237-DB38E8150525 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C5C7708B-0DD4-4506-A7C3-BE212642B4D4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 97B2B55B-19A8-4F83-83D8-E415AEA77C88 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 23281F51-E218-43E1-85C0-D0F90212A67A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7C40724E-0E05-4452-9969-5AA8DD379FEB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 705E1D69-BC0F-45EA-B5FF-0ACD303DC4F7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4C278FFC-8A0E-4CC6-B8B8-59EC22610E7F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3BEE57DC-0991-4B80-9E7B-008FCF0D9356 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 88AB582D-EFE5-4B6E-98C6-6B61CCA9CEDF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 53013E43-1D28-4EC5-8B06-643371209180 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2B2107AF-5FA4-4CCC-8256-8119D0542CEB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0E4B00BE-99A9-4D8B-A178-72760DC2CBF4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9D2EB50D-6164-4FF1-87EE-66454A6A788A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FE6EE56B-00DF-49CC-8532-66F37A215EA3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E63800CB-D60D-4080-9226-73066C17E6CE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C4037DA2-CA78-438C-AE18-27CF8236DA31 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7C0C923B-6FB3-491B-A7C9-D81FBE4FE2EC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 553CB8E2-66E9-404F-872D-2D10515B155A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 75E42558-A98C-463F-83CA-4F9BC03D48D3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 05D08DCE-3785-4175-9E16-CFAD9C9C62DD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5E08B823-17FB-4D87-8423-5178970270D5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2767FC95-BBC3-4B37-8EEC-717AB722DD11 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 57233996-755D-4D18-BEDF-D309F05E03A5 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-08-05 '-XMP-ph:RideName=Pontos de Sela da Média Leste' -XMP-ph:RideDate=2025-08-05 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=Pontos de Sela da Média Leste' '-XMP-dc:Subject+=Pedal Hidrográfico' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === Contornar Paraisópolis — 5 foto(s) ===
DEST='/Users/danlessa/pedais/2025-09-02 - Contornar Paraisópolis'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 47FAD3D9-B898-4E69-B356-4CD1767483D7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CEC8F14E-2C7C-49DE-9DBC-F072E678D153 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6B3A32FB-B6D4-4DAA-9DD2-64777DA0FDD2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E4FA418D-CE3A-4AF6-B486-1D2F21DD5D8B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 63DA00B5-1DF4-4EAA-8512-0E5E2DF9BC57 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-09-02 '-XMP-ph:RideName=Contornar Paraisópolis' -XMP-ph:RideDate=2025-09-02 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=Contornar Paraisópolis' '-XMP-dc:Subject+=Pedal Hidrográfico' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 54 — 59 foto(s) ===
DEST='/Users/danlessa/pedais/2025-09-09 - PH 54 - 1 ano'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 757EBD93-EEB5-425B-991D-5420C507E757 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 527172FC-E450-4DCB-B861-6174A38B2218 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 05FAE6F1-C85C-440D-8943-A927BCBEA8B3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C5C90419-AEBB-421B-B22A-D3B8FBCCE929 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6D01B489-90A0-4C0B-8207-96F3943F9E7F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 694D56A1-F6D7-4B76-AD45-AC532EF24C41 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5AC42401-1D14-42C1-AE32-A5E848C0119B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D6BF9C31-FE9A-4211-BC20-BE493E8AE048 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1A5F911C-9C05-4F35-B51C-D915C2E9B4B8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B2A58D4A-0082-4E24-98C1-B4E77A53E236 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 35BC43ED-735D-453C-BC71-FCC0EFBEC061 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5981C576-D1DA-4BF6-A89F-59344676FE35 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 351D5547-C931-43B6-95DA-7EA1FF65AA48 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4B57AE46-0675-487C-B237-CA14876B4AF3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E435F40E-4794-4A37-82CE-7FFDEF56CEB0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4AABACA1-B21C-4703-BD15-A2F560AF2143 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 68B4C147-2552-4B2D-8FE2-3FDAA826C273 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E06DD87B-6761-4FF7-8223-A17DB8DE2926 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5A4DA788-E5E4-4CF8-8DEE-44E734B11B08 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B1A9381F-ECBA-4FE0-BC5A-918493FD120E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 20CFDD9F-5F34-4D41-92B5-153492758D09 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6952ABF6-8F89-4951-BC26-B2004341515F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C70C054E-C67B-4495-AB4F-01984EE871F0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 652826EB-D639-47FE-BA4E-7F87485D66F9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AB61E0E9-BDE1-45B1-B8FD-16B6603AD2E3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 43CD56C4-AD40-449E-9DEA-D26E6A2D10BC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C663CB48-5601-4081-83AB-0AB1D536E882 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DF46EC0C-19B9-46F1-9407-255FC070F4AC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0D6010FB-5542-458C-B8A9-F130E7D39265 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C6869F0E-2461-4042-AAC3-62E4CEF284B7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F12A2A6A-524C-41F5-8500-4E59F88C0D65 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3B005609-A72E-4D32-A8FF-710042FC6DF7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5E634344-66D0-4DFC-9088-2C51C98BBF5B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D2AA36F7-B8E5-476C-A76C-AAFA35204FBE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 870B1316-9081-4683-88B9-B66228C15FFF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3F38C412-57B2-4005-8AEE-0083BC4DA4E7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D840C679-E8EE-4391-BF11-86B0D469B3E2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3AFE30EE-98E2-4C75-9FDB-CDF746A2DBDB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 514C2A61-36EA-4B56-8CE6-25B7EC5FAFD5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1E784872-A09E-415B-AB5E-01F7AD97FA99 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2DCE82EC-5281-40E0-8F91-1C48C8A0D08A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BE1E1AA1-6AA7-437C-98FC-77EBADD9F503 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 436263D1-24A2-4782-9659-0A8AE4128BAC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 61F931C1-2CF2-4B5D-9898-CCF578B67A71 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 218F69CC-383F-4187-B269-2B3C90A0B3AE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CB86D969-75EF-45C5-8F17-7176E56D77EE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3DD79E75-3A30-44FE-B508-995A636BFD27 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6D8EFDBD-D336-49A8-9739-68D2898F0950 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FDC357EE-CA84-4864-94A9-006E2E8EFB87 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E842F12D-7DE5-4C93-9650-E85502C35AA3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D821D905-8034-4766-82EA-C7C291867DAD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 90B44969-DE33-449B-B6FE-07485437AED6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FC0D6781-E09C-4A0A-B0D5-798DFC0CB17F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FB69DF12-3FED-4DD8-824A-ABA4E5A873E3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AEF83FA6-FC54-49F3-A1DC-7B8678728D5E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 56219BB9-9748-41E4-9F27-351678FDFCAE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E4152E3F-D7DC-4FFA-AC35-0BE29647508E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AFA40F12-9F09-4862-871E-12D8348EBDD6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EDA4AF48-0F70-4EB9-85E9-D5DD9F1248E1 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-09-09 '-XMP-ph:RideName=1 ano' -XMP-ph:RideDate=2025-09-09 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 54 — 1 ano' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 54' '-XMP-dc:Subject+=PH 54' '-XMP-ph:RideCodes+=PH 54' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 55 — 79 foto(s) ===
DEST='/Users/danlessa/pedais/2025-09-16 - PH 55 - Ilhota da Guapira e Alto da Cangaíba'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid C18022E8-D64D-4DE3-ACAA-188DC675BFD8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 67D17610-76A2-4CFA-B6F7-CD6C51947642 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 693CC660-4622-4072-8DD2-387183F1B03F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3189DF74-EF55-476F-969A-11A30E7E6166 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3DE6A11D-07CC-4616-9C9F-C392E334F594 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 73CF2AF3-31D7-4F00-8185-8F685718A38F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CB8DC860-AACA-4BE6-B09B-9E1BB79E7515 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AAE4BF50-823E-4190-8B15-DBB7953013E2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 28B1E4F9-263B-4041-8734-B5A94C6A9EC7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 43914361-011C-4AB0-8450-324DDFA29DAC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 63DF0AFD-EAFD-4B68-8D01-0C46CE9C4531 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0B78A72D-3C9B-4D98-805E-AF69D20A10EF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 37E15554-6BB7-42EC-9387-198C90D17A19 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7950D160-099E-4930-8953-4CE53619031F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 765CE5DB-9457-459E-A5DB-8F689A3B6889 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2FD75BFF-5C72-4020-A1DD-CD0DEB0AE218 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 871F58D8-2BD9-4510-B965-55B312976F42 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9B1ADDE1-EB16-4462-A8FF-CA33085F2034 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4CEFA4CD-804F-467A-8B0A-BC33AFD5CE42 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F26091CE-A79A-4051-8D5B-CDC0A8661C51 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 88025B0C-6073-4877-88C9-B9F3F7CE9ACB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9E0A914C-ED47-4056-99DB-EEEB35B0BA04 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FD039D95-EE46-4188-803B-8E6519597B9D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2F64BE31-85BC-4533-A020-072C681CBE86 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6B36ED2B-DF04-4CEA-9A0E-22836C3604DC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 19BC9F7C-DB73-43A1-8AA4-0DC6249FF379 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4F94C2D8-F71D-40DB-BE69-37B01410DA8E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8061E9C0-A47D-4766-AB7B-EC871380B08B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7EFB61AA-2ED4-4AA1-90D6-3DA8D458CCD2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BD04E87D-C093-4A1C-B115-E6AA774F414F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1AB0B23B-5F71-4C8A-AC8A-CBB0DF7D35ED --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8B71BB9C-C3FE-4EE5-AF4C-070B17549F19 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DC01A29F-2B89-4683-B7D3-41DCA1E5FF7D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C508BBE0-110E-433F-B448-870F61FC4E39 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 725CCD10-D580-4209-B541-6DF4640F9AE9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4277F020-6847-46B0-AB5B-0F994D16E60C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DEAEDEA0-6B4B-4E33-A4DE-03A1EAA45F32 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EF44A429-2321-4E3A-B634-290D82306A84 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6B1E88AE-441B-4E0C-A0ED-DC2DBF42CB12 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3C6AAB47-A511-4B20-803F-FC996A73656A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B9E1D626-5133-44F1-9E21-F65B421EA3EE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 37C01547-C1EE-4BF9-AA88-6FA084D6396C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DCEE9ECF-2DFA-4E31-AC4B-E1C01AAA4C29 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 71E1889B-AF62-4191-A8DE-6FF6BEA0A804 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 934D8F27-1A7E-44EF-8E84-4E2A293663EF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CEEDDCAF-4D6E-45CA-A128-F5B7FBA1CA8B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A5C86C30-D6A7-4395-AEE6-856D86BA19E7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E97CACDD-8D8E-4D7E-93EC-46D90BC5E39D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0E757C50-1371-4E76-935F-C1F83FC57098 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 55F69A9A-D012-498E-B067-75A7098795AD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1BB10300-07F3-4B3A-A539-ED93D591E161 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 89D9AECC-0CBC-4F8A-91EA-3B73A81E45FE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 843C27A3-9E08-47E7-8DBC-EE8500E75334 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3808FEE3-B059-418E-AD0F-AB5D82DE831D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7CABF6BE-25AE-451F-9165-B2E7D1211583 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 63F06717-5FCB-456F-912D-4079A8A80BEA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ED234A11-5DC3-404A-A64B-9BEEC5505246 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9BA6D5A7-89E5-46B2-BE9A-379317995EF5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2A3C33BD-7052-40F7-A916-73DEB8EE0FCF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B67F6B08-B75E-4F37-8F85-FB30E2819D47 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5684A407-E9C0-45D8-9B38-E61EE9BB498A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FC145271-C4B5-4A6E-B2B4-5EEF77AFD79B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DFC483E7-C85F-4B9B-9577-5B8AB03E1947 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4CB765EE-601D-46B6-A10E-B5B3E433C26A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8FA96DF8-2354-4249-9EB2-C09404F20B26 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 31D38F2E-1F27-4C53-99C8-FB6CFBC4752E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 862F7BB8-3DCE-4636-BEE3-21E547AC7A8E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 01A02049-54BD-4E08-97A9-75577026E591 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4CC7FC9E-DDBF-408E-90EC-BD89BC2FB99D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E6784C5F-4362-4D5C-896E-CE707A9608EB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FCAD6655-99CF-4C62-B83C-2D9B1DA55A48 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7DE6F7CA-F5DD-42BC-BE90-BFEEC957BC1E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8CC20AAD-2C9F-4380-BB3D-080FEEA94885 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4DC5CBD7-4C29-4BCA-ACBF-E30ABB9FBD04 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 304449E2-18A7-49AB-B94D-6838FA638A51 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8BA9D234-94B3-406D-80EB-F168C5B11C91 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CBD75690-9B6D-4E4A-AA95-A05004602F45 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5E56B514-197C-425D-A9D4-A54D1D8E35BB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FFA81CA2-9A37-410F-B1D3-92A21068672B --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-09-16 '-XMP-ph:RideName=Ilhota da Guapira e Alto da Cangaíba' -XMP-ph:RideDate=2025-09-16 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 55 — Ilhota da Guapira e Alto da Cangaíba' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 55' '-XMP-dc:Subject+=PH 55' '-XMP-ph:RideCodes+=PH 55' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 56 — 318 foto(s) ===
DEST='/Users/danlessa/pedais/2025-09-21 - PH 56 - O Trem e o Meteoro'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 5926C348-8C61-4028-89A0-CFF816710DAE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1BDAE5DB-24C7-473D-B3AB-D4325C032974 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9BCFCD7E-2CC2-47EF-94D8-8AC9569A0C38 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 083A15E6-0B1B-42A6-AE5B-08AE843903D1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 36FB8A1F-22AA-4CA8-BF19-64350E58CFDB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1FFCB27E-67A3-461E-91B3-DBE7A832B8BB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B172DE85-038F-4589-8F0B-762975EB4932 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F6DBEA91-F7CE-40CF-A3B1-CA11F2F7BAD0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A4BA7A7D-2FF3-4EB8-9A19-4A1FD999366B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C3BDABC7-21C0-42B7-A7C1-2F3BCA72123B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7DDE319E-3250-40CB-A400-C4E8378BD749 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AEE01973-1E89-41DA-B013-56DE9E6B2520 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DA97EEED-04AF-4752-892F-BAA018900FB3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CE05F9DF-F11C-4467-95C7-229239F202FE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FE68514E-FB8F-4B1F-88AA-AC67BAA69DD9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 99013B72-7852-4E77-B169-93D4A96DE482 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1B2CA0FD-A683-48FD-AEBC-F9A8C85E8611 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 13443947-F325-4C1C-8B77-C92DA791A610 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 47929A01-B44C-4EA4-98B4-424DE3F3BD00 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 587AB980-0C76-4165-864D-0267A54FFA9F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 90D70551-2712-4475-80E2-4BD73F125DC0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B339C036-786A-42A0-B8C4-4301D2E2968B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7C72606A-C6F4-4E98-9E81-1EBB4A5772B2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AC892BDB-37C5-4AAB-B011-A8F84DF51236 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7B33A941-4A37-4335-A493-741A03AA1E23 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 29FCFA0E-A7E9-4F0F-B4AD-1B20E60D6E1F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C2E9B367-2918-4985-85EB-1DD24CF3733B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A3CB137B-3662-480F-B46A-3A13E52A3EB1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E8133676-29F2-4F21-9510-7218EA79FE5C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DD18476C-A05E-4F9E-A78E-D77FED751772 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D6EB7842-5877-42FD-B0B9-AC98F06166EC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2741D0BD-1A62-4851-95EC-3DEC334C83E2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E9E3785D-1FA1-4D06-A536-E5F14D850EB3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EE78DC5E-6DE0-44E9-A608-79358983731E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 92DA2720-5C24-4674-92D8-0F4FFE2CEB01 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1EE6AA62-14DC-4884-8B41-5076FE75B875 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9A6B3676-0425-422A-8737-5022EF8BDD97 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 41CF5874-9FF9-46E8-9969-3584C21B5F18 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6D3B9E2D-DDD6-4418-8394-A474B1FF1A0F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ED0B14DB-07D2-4101-ADB5-043B1D570BCA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E7E24E40-1DA4-4FFA-A7DD-64C39055559E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 47FA7F0B-FCAC-40CF-BD5B-DC4C9D7DD86C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8B4A03B4-41EE-46B7-8DC9-B6A2DE10C57D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B2F6605F-B742-4907-8AC7-6A6B875439C6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3D461D98-2B11-490D-A6B3-38A437B5D72A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D4412EA7-2393-4FCA-BB69-5EDD3FB6D99D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 43357204-B9B9-45B5-A792-82F568193379 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9F521473-20C0-4902-85CF-09C01C3AFA22 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CA0E6F30-2904-4C5E-B121-0240171F2DB2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 66B13E6B-BB62-42F7-A20D-626117483EBC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 38118616-1F52-4DB5-ABCB-9D838808EB1D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 04078C75-3CA4-436D-9416-9B91176061DB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 28FFE944-E48D-49B6-A1D8-98EFAFBD20F9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9314246C-CDA7-4358-82D7-6956B9463B8B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 72433464-B77E-4786-A6EA-88BC1D65E466 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C7F0D92F-59D0-4170-B9E8-5EA2BB1CB04A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 750F49EE-9FD0-4C5C-89CF-40D63770B99B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 303C5E38-4083-4692-A244-28A060313B3E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 74F2D087-DF62-497A-8A55-F8F44290DCA0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 08397417-645A-4DAA-A3F6-7D9BCAA2661D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F9B8FDB9-2FBC-4627-AEEC-4ACB37C573B4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C24026A4-53DE-4B16-9803-9F598DEFC7BA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E32980D4-042F-4893-8FB2-ED955A70579D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 378666D9-B7A3-4F9B-9995-561FB7A413C9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A97AB2A1-949F-4187-B492-8F6AB681FC73 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 32A452AB-4FE2-4AF5-B28B-3190FE19EF8B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8DA32AE6-A417-4BC7-8C63-E0534A8DF52E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 71B4F912-0C1F-455D-BF56-F6F1AF32C82E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CDEF22A3-CA6F-4AA0-8A7D-A8F96106162B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8F88E987-FED0-46F9-B6CC-F69B35D5CAD0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9B8D92D6-68F8-41E6-8EAD-C630525EB174 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1519AB47-F986-4C18-961E-E4CE73F0FD39 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B24E9EBF-7381-4BE9-9CF5-9C087F3B2CFC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 53D84C22-E2D2-499D-A7D5-C2B14F2AB79A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B576D2EB-5B01-4641-AC58-5CFCAEBF84F0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6B631697-1096-4D5E-8739-20D16533A51E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B4D6F7F6-D9E8-429B-88F9-2B4A2FAFD88A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A15B6EBE-257C-4C59-97A4-C2A4C7F9E026 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D7EFF57D-9D46-4E39-B0B1-63A43A2E9530 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6091A963-B14A-4826-B78C-D8911755107F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DBAA325E-D534-47BB-99D0-28516EEA0592 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F3607140-CAD4-4468-8755-7EFD03A5F0E0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 72452940-3793-4834-B4A3-754CFC033E92 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A88C4608-F43D-48C4-8ABB-88CC90272F9A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1BF8C610-1370-4961-B382-F23969652DE8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CFD890CF-C986-467D-BD61-EAFFDD1AE975 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7E7CAF6D-FCDD-48EC-A5AA-5645FD3CDE63 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0B7801F4-A44E-4ED5-9708-1027202E7AB0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7D0AE6DD-9C3B-41C0-B50F-C0FE73E0A747 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 80740A0E-326C-4D46-AE1F-3BBAF65E11D3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 95917755-20FF-4881-BF40-E76C8F0AC18C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8B32373C-FB58-42BA-B7E2-88BDEACEDD78 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 589CC957-63C5-42C7-9693-78896E2D61A3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2FB37D17-1A06-40D3-AF68-90B8FB50545E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DD75A422-644D-49CE-ACF4-1488D3456E4F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 96C5D5BB-3A2C-4FC9-8719-97623B778F91 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EDF6EF33-BFD1-4208-A89E-D3917331D975 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3A5A41A9-E9F2-4282-ADE0-37E7616C1AE2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 06EBDD45-EF4F-4C88-A948-ECF35D719AF2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 867E83B1-52B0-4C70-8C47-8206D0FC9B0F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C41272E3-1AA8-41F7-AEB1-3DB20F013D22 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6157797E-C219-405F-9E91-CF268EDC705F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 477FC141-D5F4-4CEB-AC63-4F343C437999 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 96DC011B-918B-4EF5-B605-27CC0E19541A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A285D15A-0FC7-4CF6-A637-D52B3556F69A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 36BCDFDE-A706-4E14-9E62-AAC068FBC66F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9417AD69-85E0-4D2A-91F8-489DF8C0470E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 23C479F7-3151-4EF4-8F5C-793AB3A7F9A3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B7269430-942A-406E-BEC2-E75392A9422E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 65C67468-E732-4D74-B531-9B0F8FA2BE36 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 23002B6F-ECC8-4A11-9047-C822C92068DE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B98B3B5F-B6C0-4031-A3E2-8B16E88A8001 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5B2774D3-ABCA-466A-9F29-21F8C0CDB0BD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 57868781-CAF1-4BA3-85FB-77F819690EFF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5A8EDF89-99C3-476A-9F0F-668B067989C2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 71F9FEF3-B943-4A50-BE46-EC60067255FD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7C359421-1ACC-499F-B67C-FE450B310150 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8A69B86C-7F64-45ED-AE06-73F7D0B8311E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8CF09856-7F9E-4AB2-8EE0-C686D0D4A88D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3390A84A-2D39-4B02-AA17-525029556EE9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7C165B29-FEEB-4973-87C3-A21954F0C128 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EE77E75F-1A21-4555-9E5C-01391B93309A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 941E01B5-68A6-4732-B1D6-B4BCBF7F2782 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8E6F242C-825E-4B23-B12F-DAD0AC4DCB30 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B6AA9E9E-0B3D-4757-A0CA-5D167A085ED7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4F5E1731-E6FE-4209-A038-68C2BF390A90 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E627B683-D967-4455-9995-66401C429B37 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5772918C-B8F9-406F-AAB5-BB6B25A47B3E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FDCF9089-2C24-450D-B1F7-AF3C752733D2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7C51A794-939D-43CD-A414-4962419E96E7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AC0D4F1B-EFB3-4447-B1CD-12C26D37A20B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 299FBD0A-1E3C-458F-A25B-A70C21663D05 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 031B0363-29E6-4F8D-B688-AD5048FA8943 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3C7C5507-75B0-449B-9CD3-EC4894CAE34F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E685B14C-7EF6-469A-BEF6-39ED30A8FA35 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 89B1CE0F-A2A6-4CF0-8BB3-4358EFBA8803 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E94F27AF-0AE3-46A4-A9A2-DFF4F5EFA1EF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 107986EC-A044-4FBA-BAF8-4240FB2D043D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A0E0B91A-C7F5-41DC-9CC0-6919D6CE2156 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E981E207-C1B1-4F0D-98EB-3056BB8CAF14 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 76F4D2A4-414A-461E-85E6-5D49B92E823B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 128349FA-2071-4476-AEB9-1AFAB3C542C6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1BFE1DDB-3421-4173-9FC3-B631E968DF3A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CE31E42B-FC61-4445-81C3-6CA6A0FA1132 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8A56DEE4-4BF6-40B7-A3DA-849725EE8D3F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EF4231EE-DAB0-435D-8ECF-36E07998E015 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B60B3EEF-CE70-47A2-84F6-A13EA8F9C050 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7D8DC95B-0182-4579-8FEB-6587E8E4EE19 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A2FEFC06-69BF-4FEC-B427-F8F16305DBE5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2B989F50-CFC7-458C-BD14-B23B63499FD5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 13AE8BC4-42D7-4B78-9883-49F34B9E4A21 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 617ABEDE-C1C1-452A-B001-139F058C674B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 99A851B6-F4D3-45E3-B18A-457C17A67D24 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9B2BB96C-11D3-4164-8B3C-429DDEF3FB1A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 47478F89-090A-43D5-B20D-0A3325491E21 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7EE66762-1508-4670-B37E-D13A3E55FF35 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6B94A3FE-6D2F-4A28-AC9F-5EE2CE54B52A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3CDADE0A-9166-4DB5-A656-DF5889725A17 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DA8589ED-2A30-4AAB-9380-565A29ADBB25 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 70C3D58C-F2DC-4DFC-887A-FB5DD7086EA7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EC110601-483A-44BE-853D-967FC74D0ECD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3983B94B-E589-4FFD-BC83-26757FB3946C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3B464498-CFDE-4E2F-A5FE-EB460E81305F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AF37868E-227C-4829-9D62-87F2A4F2F8BC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F1015424-F1CA-4377-B206-E24BA8E992A5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 51B8B0C4-6919-4D1D-AADE-6CD2604FDE75 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F1F0F9C0-8488-4134-AF16-BD2754447DCF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2EDD3C44-9358-4345-912A-955BB796CCC3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F4EB5758-40BA-42BE-B6F9-71354622157C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7AC0630B-87B3-4AC1-8BEB-C5B5E34F41FA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F5F192A5-5546-497A-B5AA-F4C2F4FDC8C1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CF5F12FD-E83A-43AE-AE11-C32F1561A428 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2EE4011A-60A9-467A-9301-05B5BC0092D3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 727192B5-8466-4B27-A361-ECBC3F8C65EA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0D23D7E1-7EA5-458F-93E1-3EB19CDA70E8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C1AFF66F-F8BB-43E0-BC71-5D6DCA49926C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D11BB0E0-430F-466C-BFDC-EED85A4AC73E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 069E9FC1-0903-4FA6-AD7D-C022F44CE129 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9F8CF145-6B2A-47C6-9727-4CBF3D9C98BB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3E057C9D-C2E3-454A-B53D-109276EB5E39 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F1013515-6477-44FD-8A69-07372D792734 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A945F66A-4F22-40AB-BE83-431E90A48196 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F3627E64-F161-4F52-8BBA-D474E1D5F891 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 421527DA-C4A1-4DB9-A803-4212D838D9F5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 65AF918A-150E-4A1B-871B-E3E3D608A8B2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8580117E-1A36-46DC-84FB-41F152236A29 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 85280682-4965-4EB5-83E4-3E0032EE10D0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 81C08CFD-1CC4-40B7-8D88-212A11957147 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4F8F9AA3-FB78-4010-866D-E4C42BDA7719 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EC99D69C-622F-4234-B867-EC56D712AAAC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CABFB844-2317-4BEF-9D61-910E0BFF148B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 89EE6DDC-3BDB-4248-8A69-B6F22AA8F58B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6B9D5BAE-5B0D-4B67-A1DF-C87FB88547CE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D2C50E3F-67D5-462A-891F-BEF9CD0547A3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E2FACB91-D0CF-4FC5-8EDF-38D1F1436F54 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6C03281F-7AF3-4F1E-85DA-441BA349D834 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AB365D9D-C745-4E4D-9918-D38925BE79C5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 931DE160-427D-4A1C-802B-565BE18EB3C8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5F8A9F1C-4CFC-4532-904F-98084957DA7C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5C8F82E4-8B20-4783-AF86-6D928D124950 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 493816EC-4E9E-471C-80CE-A3100D483CBB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C9FDF126-AE6F-42B6-90D7-B62D3941BB0E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 47F2B9DA-A4F2-4D64-9BA5-5032D2A249B6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9A0C974D-8037-4C0F-BC29-DE85E5A2FDEC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 62367CA2-7651-43EE-B600-525579FF9550 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C527A0CA-097E-4A3D-AEC4-17BAAE9AE1A1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2AE6E3BC-13A3-4834-90AD-993FD7F000F1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 85AAD584-A1DC-4628-BEBC-2D4D3CF3DC2B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 00BE3AE3-4D45-4579-9182-D2C2747E3F89 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F104DC56-5847-4EC9-8B55-BF7C275E1855 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CD0D29A6-958A-4771-AEA0-1198835386B5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 50020536-544D-4ADA-8D31-8865B34DED89 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 823FC1DB-4135-40AC-96CD-8240D0330170 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4853CD72-639F-45C3-B771-7AF78D4B3B48 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4917076A-238F-489C-BB40-7A17F988B0C6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AF366FFD-AAC0-4F97-BF78-7F2BF69C09B4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3195AC62-D76B-4C79-B5A0-7F6C20F1B0A1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D04B271E-A46B-4B73-8EF7-4B805A3A8B62 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 01A2C47A-DCFB-4793-A96E-D497737D0E7B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DE974EB1-7AB2-4F85-B9FE-2197D78C04FB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FA3374BA-C05A-418E-B6E9-BE1259ED0575 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1510EBF2-A68E-4255-BBF4-7EF181DA2B14 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 04616F36-E5B8-477A-9C8A-CF2E50AB39DA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9D5ED48A-0E02-4D30-B25F-0F81BDACA51E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C4819B52-DF68-4489-9FFE-20098BA523F1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F9BF9053-8F0E-4C4A-B5B7-FCDECCA29247 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6B121F62-5B96-455E-9469-F821D40B6AF5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C44508AA-05DC-4C0E-9C88-5EB770D03A8B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A8160407-D89D-4E0B-832F-6B6B9B1171B2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E86DAD7F-8C94-4D20-95D7-878F36DE7B14 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 55EE9BB2-916E-42AF-B5D1-2BF351D86D73 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1163814C-22DF-477C-950A-E8D928893438 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5585FA6B-E583-4CA5-A19A-125390CDA62E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7A51FB2A-108E-4482-A8CD-918EE588E5BA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 32577EB3-02C1-4721-9414-AB151787A226 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4E7F99A9-B338-4FF0-BD9C-6620273D16AE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 89ED2259-00C4-4486-A67A-88337C0C0283 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AD6BE600-90EA-48EF-81E6-534CDAB178D5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CAED37A3-963F-4713-85A2-568889657DA2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B7EC9EE3-60B1-4554-92CF-5D8CA93ED5B1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C4B59780-C3B3-420B-8C02-A6715F6998C2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B85DB2FA-AB8B-4537-9A0C-3C0B7043CE65 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4B1C5E17-8CF1-4B87-8DB3-57D1C17A7D03 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 99604B5A-947D-4333-99D7-0645901AEC23 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 69E27A7D-AF5B-4926-8648-470058EE36D6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6FFCEBDD-5FF4-45E2-B5EF-339FC431ED9E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F0793467-C604-4D1C-996D-984E098722CB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B1C77D70-ED64-433D-8BA9-5C49A3292C63 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ABF3711F-5288-410A-8B8B-32F28CBA4DB7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 45B59F2B-69E1-4FBD-80DD-12D2863AAD90 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A7A159EA-D942-4C53-A332-69EE1A2D9880 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A9D44D25-DD5F-4AB2-87A3-FEC532DA9246 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8C456236-BC8E-4557-B5B0-104D74D934B3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 66741473-2023-4064-836B-3AE461721EDE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9F64794C-16EE-48E6-949C-8A93D1318331 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 66793D2F-DB75-4F46-B3AF-075AF4ED8DBC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3A874823-BE07-413D-BAC5-820576462C82 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1E611A72-32B8-430F-B534-AD5E54061B52 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B3C88601-5B9C-40E8-9FA6-BE671C4CB247 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 40752A08-DA1D-45C6-AEBE-46A1B659DEE9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E98080C2-F7FC-482A-A9B0-BC295EC69E97 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2B8EC67E-8C73-4C49-B5CB-AEF514ACCC2E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DA29136C-CE40-419E-A0E5-D4F7ED28A776 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3CA6109B-E70C-45C0-904E-F33AF8DE3065 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D9F41329-0E52-459C-B1C9-9E6474A25E6D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5866BE78-7D1D-4F80-8F3B-3B456E407AA1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 08CB006C-A612-443F-BBA3-3B5991644FE7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 76494629-05AD-4A3A-80F2-11971788245A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 19130F7D-FE3D-4752-B86B-30FB3F00772C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 61277EF4-EDE4-4FCF-B01B-DD2F6365C98F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F2E1A4D7-71D4-41F2-BAE2-7E643536EE68 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 23C8557F-ACF0-43F7-B897-42A8C188C018 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9E3A9CEB-F813-4B3A-AE02-CE6D1F9A0141 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B21D245E-FB66-44EF-B040-CB0B178987C7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3D30E0BD-56D0-472D-B8AB-84A56957E3B8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 07941FD5-7BC6-4A8C-B769-B70C2F013408 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 08F970CE-5331-4448-A3B4-A65E8643AD39 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 200CE00E-1FF5-4684-82B6-F7402415A17B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8BECAB55-E898-48AD-B2BA-0FDEF0459AB5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 01E7F6C9-6982-451B-BCC9-7F22C2186D00 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 311BF56D-BB1C-42EC-A4E9-9C3792EBE84D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2647DBD5-347D-4EEE-B7EA-E35C14099E4E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F75A8836-9844-45B5-B785-F41B5921D898 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A435CDB0-C0AA-4DED-9228-15E0EE95F63B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0BE1CE6D-4A82-4FFE-8EF0-B1E6BE5CE4B8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A6A80F43-6327-469F-BCF8-3496D6B59530 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 90DE1FE2-5E8E-407E-820C-52307BD67321 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FB424E8F-1B46-4534-BEFE-A1E417025E27 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A2CFC223-B4C7-4853-83B7-1EFDEC748A7C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 14964FC2-01FB-44D7-82AA-F14E5E86A1F2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D7EE430E-398D-435C-B2D4-251A91C9359E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9876CC90-0A9C-4753-9DDA-8EBEDC526F19 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E0083D57-1417-420D-9EF2-14C0485DD980 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E48A6FF0-0B5C-4E8B-B603-F502148A3EB1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AB45ADA5-ECB5-451B-B8A3-2E69DF58FF57 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 89D103E5-1DA6-4D6B-B64F-747CC1EC7429 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D335389E-A4C5-431F-BFF6-2CF523DEE8A6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 75C1571F-F3E5-4FB9-A746-2A91723733C1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A4D9CB3A-CD48-4AC0-879D-64F356156A90 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DB1CDF2E-1BC2-4606-AC0C-C37FDA111049 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ECAD23B1-98F0-4E86-B975-07139AB7BBCC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 28A1CE69-DAF0-4590-8406-651A3528F06A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7EDDA202-8227-421A-ACB2-FE04A9AF753F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F805A19C-C6A8-4782-9944-D36305C483A0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 06AB51E8-2806-49E4-B2A0-890B203F3B83 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 49F38C6F-A957-4943-833E-85D8B2A6A7D2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D4DCF45C-A323-498C-AA24-80CE6D5486BD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 326ADA9E-2332-4A85-845F-C9D25F32D79D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7671E0F4-7306-48DC-8349-977A0AE8E3D8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 552EB75A-1BE7-46D1-8789-7BC67BCC5D8D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9BD82EFE-858E-4FCD-83D6-D6F3C4CE41F3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 78C2681B-0A32-43F0-B953-E27CC9235759 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 606B91D1-F7EB-4029-A381-778B3FBAE753 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B24E3AA9-596A-4C92-9371-2A52E6CE5022 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 801BFCE9-9B88-4DA2-8E69-27253CB63ACF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B7945900-CF34-4D24-9A8D-DD42079B6677 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BFE2B361-CB98-4BD3-8BFC-45C9889B0C43 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 74E56F8C-EBC2-4423-99E3-FC0D20A96DC7 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-09-21 '-XMP-ph:RideName=O Trem e o Meteoro' -XMP-ph:RideDate=2025-09-21 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 56 — O Trem e o Meteoro' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 56' '-XMP-dc:Subject+=PH 56' '-XMP-ph:RideCodes+=PH 56' '-XMP-ph:RideCodes+=S 6' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 59 — 1 foto(s) ===
DEST='/Users/danlessa/pedais/2025-10-07 - PH 59 - Bico do Caaguaçu'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 3E1AB452-09B9-435A-9F87-78531F139147 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-10-07 '-XMP-ph:RideName=Bico do Caaguaçu' -XMP-ph:RideDate=2025-10-07 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 59 — Bico do Caaguaçu' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 59' '-XMP-dc:Subject+=PH 59' '-XMP-ph:RideCodes+=PH 59' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 61 — 140 foto(s) ===
DEST='/Users/danlessa/pedais/2025-10-17 - PH 61 - Oakland- Lake Merritt Up and down stream with a diversion by the Saus'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 617D8C9A-9453-4A2C-ABD8-0D59F9D5DCC6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0CAC8C32-4243-467C-BBFE-62E8CAFC3017 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C5B2AFCA-7FEF-4D68-857B-5E7A723DDD62 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 668269E6-7089-43E8-B568-979E17E0C597 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F05CD6B4-934B-44A9-9633-0CF3415FCAA4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B2FCC399-107F-4EC8-BF71-0DC236C95DDE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 865BEF81-93BE-4E56-AEB2-56FDFBD63F82 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0959D5C9-2677-439E-AD52-E58EF261B8E5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B1843B9D-472C-4816-8177-A764F7DE9FC2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 85F7CA58-2A6A-4307-A7D4-45BBE5D93599 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 22C3CF4C-E8A9-4EE0-8CE4-B65D07522AEE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2F59C850-F362-4F87-83FA-4636E230D395 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 98515BE6-6D38-4C90-904A-4FC804AAB417 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 417FAB75-8119-420F-AF8B-53E38ED59A1E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 602E53EC-98AB-4248-BAC0-D40504C7A4B6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 52F7CE08-8DA1-45D3-BE48-758B08E252F7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D04F1D9F-7316-445C-A498-C808EE8EBD11 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 98DB9B32-AE69-45A7-89BF-D3517676DF96 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 17323BBB-81CD-4287-8927-FBF0E0216552 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 69EE2661-BD05-488B-A87A-DFAAB1E85C3A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9488B60F-476D-4B77-9CAC-FC906C2AED51 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4555FB53-0E51-4C64-84FF-B7380CDBEFBC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 84320C32-1F75-4DB7-A20D-F57D37E8DE5D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BE1E6076-E6F7-425C-8E4C-9755C5B86AA3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 79CE9C48-9C18-4A9A-9D6C-57E64CC51C89 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5E598A26-EFDA-4786-9AD7-B75392535403 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A2E111FA-2D5C-4C29-A102-EBA902B062D9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5BF21502-B5AF-42E2-8CED-31276DEE6016 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BC3271FD-D595-42DB-A672-D2052E398C13 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1A796451-1CCD-4DAD-AD83-042460148D82 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CFB09B9F-C635-4CC0-831E-20E3224C7A1B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7EFDCAEC-FA87-49AC-945B-8A651796C75B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 09FE6AD2-F7EF-472C-A7B1-414B303DFC5A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 75A61E08-F1E2-4887-8C03-6A6AF4C56C9B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C49EF21C-E780-42A2-9960-0E8A728FB7CC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BB1F1EF6-0CA8-4934-AFD0-6CD63287A8D0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3EAAEA2A-CBC4-440E-AD22-DED94E465B52 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9384574E-C18F-4A80-AD72-28392723F167 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 13DFB07E-16C2-45AA-BE37-53B77346B42E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C832DD44-1EDD-4149-8DDA-0B67BEEEDD37 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B3C012BC-C0EA-4495-B4EF-8440F8B858C0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4DCE9580-3361-4ED3-88C5-FD74B1AD4FEA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3C53CABA-3F23-413E-8FE8-BB67A1E9AE3B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DD0B2444-EB21-4452-89A0-6BD09447D619 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BC8BEF3C-E7EA-4D7F-81E7-9F81E054AAF7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0A0A471B-CB60-471A-8053-BA0FEAFA27AC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CB32C634-68E5-4508-B839-D852851F0D0D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 738A36A3-6C36-42DE-AC1A-EECC75E97567 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EB203DEC-070A-4718-8EE6-19D20E8912FC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F596CC34-8B84-4D1D-85F8-541CFCDBE65F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 89EF1C9C-B49A-4262-94E1-78308A08FA18 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 32F66745-F1BB-4A63-B62A-091B6B5360FA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 06EAEB1B-732E-42DC-B53A-3C8ABDA4C93F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 26BFF2CF-FC00-4D52-AF77-BD7369BDBD6A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A41F9844-408C-49AE-B035-FFF6B7C27149 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AC890E51-A274-448A-8C17-C94B672FCC2C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E957739F-E886-4739-8BB9-F1AB784AC938 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2ED7E0B6-B2E3-4775-A550-CE8B97F24C6E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E315C0F8-2B20-43E5-B905-12A80D268EEB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 318C5BC4-A4B4-47DC-A539-DF15EBB9F2E2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7B019837-A0A7-47A8-B246-1B6D29424FA7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9BA66D1A-748F-4624-8EB1-90D09E4A3850 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7A5489C8-DE65-4E73-910A-09C2B1A9BA26 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 057A89B0-9B8E-467B-BA31-62530CD6A309 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 33138D57-FFEB-4C68-917E-1B52E89C727A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F80B352B-1F63-455E-A413-586BBD403857 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6114F7D6-8561-45D5-A1C1-E94D4322E3DC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 491E89D3-4CBC-4726-B7C3-E8BDA70FACF4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D97B53E6-6C21-4BFB-BC19-99832F1022F5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CDC3F558-AF73-48B5-A95E-CC9A91DD3D70 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 24ECE77F-9659-4B32-816C-DFAE2C03D65D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6A218364-CBC3-4E3C-93D3-6FC0CE65F34F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A7CB869C-D05C-466E-B29E-0AAEBD15A993 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 84B2031F-39CA-446C-9E6E-C044A2C7D431 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2F5F9C6A-C002-49C1-BA8D-98B64656830D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 898DA6ED-2786-4008-B9E6-A11AE3FA36AA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DFD2A53C-768C-48A8-AD29-5B287BB86E7B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 49CEF62B-8950-49F0-BBCC-93FCC9EB92BD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0107D5BB-4F9D-4278-B6CC-BFE19FC2CD8C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 49F71CF1-467F-4FF3-BB05-CAD37549E8DB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CE1B2CCB-ED38-456B-8795-C6A72FA49CD5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 57AAFD8D-F566-40D2-9029-6B2225918B02 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5FE68F95-B2A1-476E-BF93-D64A4C6E6E6F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5D19700B-7685-4B7D-896E-259B798FB240 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3F90ECF9-D431-4898-B432-E90CFAF96B43 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6DA6F3FF-A7BA-41F6-936F-E019BDDDC5EC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 41EE2991-3A5D-4F0C-ADC5-61F9939AC4FA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 012E9264-51FD-4191-B931-0F8438E70DCF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 21709BBC-EAF0-4314-AC56-9467B7DF6377 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DC478015-9795-489E-96C8-76D18DF7DFED --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6EEFEE1F-121B-412B-8EAC-BEB2D1EE81A9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8A8B616B-7FEC-43F6-971F-13E5F8B40FAA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D0179BE4-7AAC-40A5-AFBA-9210B6EE3B0D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 777A8419-F497-46E8-B87C-47803B076D93 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 61CC6262-B094-4F13-BED8-BAA4488CE9D4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D45A37E2-C317-4404-A554-A2E25C033F37 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5FD72DC8-16DB-4182-AA99-AA50D8F14323 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5FDE3B87-AB63-4F84-9836-0AB6B010759C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BC383632-D121-4AFB-BA9F-EBDEE7129010 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 06550BE3-7D68-43B8-9DCF-721121D8D64E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D960C779-BA75-4FA1-9773-89006439FD44 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5E7BCC71-8222-4267-98F2-1EE97045CEB2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4F7B47D5-2024-4E82-94E3-DE4C89D9F2F6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 697B1EB4-8638-4E1C-8AFF-E4C01CD972FF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 38B2ACC0-C9E5-418E-842E-89A1A3A3FE3C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 58634E53-AD04-4539-9982-FD250B97AC3F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8381DEF7-93C3-4379-B41F-655527D70F81 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A26DA9D5-9FBC-4613-8072-D5FB347B689E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8A3FF0EF-C105-4496-B046-37FED73CF545 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 86C75BDA-B58F-401C-91CA-EC46B3880233 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 55F9B571-2BEB-4622-972D-7B87DEF8D983 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AF358B64-E004-4A13-A225-ACFD07B45D97 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B5CD32B8-F537-48D0-A0FE-65F409409CBA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D8CAEFAE-0030-4856-AFC9-A986F2569628 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B90F3920-0857-4E03-99B7-EB0B12752720 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0F011886-202E-4DE5-BDCB-2147C073DB92 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 69FA7961-8807-49FC-AD28-FE64CF556CC0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2937804A-5978-4098-A9E8-D5C4D55D1DBC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C66ED809-2825-4D37-9B48-334D0AF5BEBB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4806CBC0-C0E0-4756-9240-856612FEC967 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 434CD4F9-1177-4218-A490-3290275FC12E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7A9AC4B8-53EC-4543-A992-3519C38039BF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 78F81BC7-E3DC-4ACF-BCBD-A10D581751D4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D16A05E9-31B5-4BFF-87B9-0C0228072215 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4E087AC6-2E57-4EF9-B865-F24C07A3036F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3B7DA69E-138F-47C7-B787-F00D37E6EAD8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 79BA120D-F9E8-45FB-8717-CBD21677CD15 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B8C36F6D-E1E1-4165-A330-BA42ABB19DB6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 66D9F6ED-03C9-4F4E-B8DF-72FBBF902630 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8A680E58-9C98-46C2-BB0C-98D53FE19253 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A5F2E4CB-FCC7-47A2-8E8B-B4C8CFA5BE21 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2ED15BBA-A22C-4806-A172-F3DBBA83AE8C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2F2E2059-C5C1-449E-8355-4AD6F2BFD65D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 66B61632-72C3-48A4-9936-9ABE2FF994F2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5403F7C3-CCDD-43D2-A320-889C9868AC06 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 16D754D2-53DB-4039-9591-C20D7FF38008 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1F6DFED3-9968-4ED9-9DD2-9B7B71681C2E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8A996560-C951-4A33-AD80-A67233369A9F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2B778F11-217C-482B-BEC4-BE50A175651A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7AFBDF34-E97E-4BD5-9526-8BAC3FE1CC29 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-10-17 '-XMP-ph:RideName=Oakland: Lake Merritt Up and down stream with a diversion by the Sausal Canyon' -XMP-ph:RideDate=2025-10-17 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 61 — Oakland: Lake Merritt Up and down stream with a diversion by the Sausal Canyon' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 61' '-XMP-dc:Subject+=PH 61' '-XMP-ph:RideCodes+=PH 61' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 63 — 34 foto(s) ===
DEST='/Users/danlessa/pedais/2025-10-28 - PH 63 - O arco das cumeeiras do Caaguaçu'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid A8A13327-149A-4C46-ADF9-2207A2C69BC7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 62A60E52-C32C-4A82-AF2D-2BC5BD9B98F3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BDFF39BC-A62D-4687-BDC3-E759C8162ED5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 06B0EAB7-BD27-4558-87B2-094AD4118F28 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 42D1A27E-9F5E-4544-804A-EDE14D689D97 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CF1D052D-C9C5-43C9-BA7E-B64F093B8584 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 146FCC52-53FD-42E2-9D48-285865E4479F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 15809B3B-E1A7-4C3F-8972-C14D8BCF7D56 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5C60B571-D8E5-4B5C-8351-885FF5C95B5B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6EC4BD60-6267-469F-8FDF-422CE30CD81E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 94A42194-A78C-4D17-93F4-4E0B2C2757D8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ED79D1AC-D0E9-430A-8F88-047F66EA1EC7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0ED73223-56E7-4036-9230-3366A2D6CAD4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2FB01A34-C5EE-464E-A737-94661BDC030B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 18D20EFF-05A5-47E7-9908-B91E3E770838 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 241426CC-43E6-40C6-9FEF-33B8583514FC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 27AEF962-3494-4105-8E46-1583A93854C1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A7604E0C-0F61-4C70-9089-FBFC825336AE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 475DBBFA-9E91-4195-8178-337DFB34A5ED --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 86DEFE4F-8196-4532-8266-AF05D99F1339 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 12FEB3B2-F98D-4017-87DE-C0273DBAC53C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5B849CD0-8846-4AFC-BE04-CD60E4327297 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B3C405F3-5ECE-4834-8B5D-6C94ED37A445 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0BA0EF28-7782-43A9-9C7B-6EC13B39B137 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B2EDE6B9-C5F8-4938-9E59-C365B3649E15 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0B3BAB6F-6260-4E3F-B0F4-B1598502A6E4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0702AC9C-98B0-43E7-AC28-6EB61443A49D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6ABDD66E-DE64-44F9-81DE-9A9FD35028A2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 698CDC1C-DAEC-4B2F-96E5-8D78ABA49E78 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A30BAD39-4CCF-4590-9867-8B8A5A22FA06 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C1745C05-2065-4CA9-B93C-9358DC7033F2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7730836A-5CC7-4015-A197-BB2334277E96 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ECA066A0-7D78-4928-9A23-5AB1AB3CBBA1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ACFC06D7-6724-49E5-A459-D69EBB046EF9 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-10-28 '-XMP-ph:RideName=O arco das cumeeiras do Caaguaçu' -XMP-ph:RideDate=2025-10-28 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 63 — O arco das cumeeiras do Caaguaçu' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 63' '-XMP-dc:Subject+=PH 63' '-XMP-ph:RideCodes+=PH 63' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 64 — 105 foto(s) ===
DEST='/Users/danlessa/pedais/2025-11-04 - PH 64 - Pontes da Ponte Rasa via Várzea do Carandiru e Baixo Cangaíba'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid E8DBDAA1-BB77-475A-8913-EBD20A891416 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 53629068-0DAD-4597-84AA-30FD5FB06EDE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BA5FA993-DB26-444E-8D0B-EA593A463F65 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 947A9B47-65E5-42E8-BE2E-220E20E4AD5E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 549A7DA6-CBF7-46D8-B92D-758E511785BF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 80FFCC22-B4E4-44A1-A577-47F645BD0BC7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AB434D13-75F9-4F84-B9E6-F2ABE7D4E736 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F08D19BE-2DEA-440B-9ECF-F2FE5E2F692C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6F3B4F10-31A7-4FA3-8D6C-B590C86A8841 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 98BF1960-86CC-4913-82C5-CAF6485CD8A5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C0330E17-B10F-4C2E-8E41-7857C74E7FB8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FAC22A8A-D187-4DBF-AC79-0298CCEAAFFB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C87F6932-9279-49F0-865B-E121D1CFA86E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E05BBE3A-5823-4CE9-AC37-FC71645DD667 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7239D243-65BC-4065-A7D1-52564BDE2E10 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 819861E4-9D78-416A-BAED-1B2809614889 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D8C75E4C-7F26-46C5-9E1A-CC652C37CEF3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 444761D9-30CC-4874-A560-69952AC19AED --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E9A584D6-5650-46D0-B247-BBACDD936A7C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EDCFBB2E-B913-44FD-9A55-952FB615CDD2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 408EC009-FF75-479E-93A3-CEC024974D16 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F485E070-1E8B-467F-8531-66D407720972 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AEAB52FC-417B-4E8C-8551-3C1F22C17D51 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4E55EB4F-7D17-402A-A0E7-490097E78410 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 070A85D2-D513-4720-9DE9-716EFAA05311 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 63DC2976-B4AE-4049-A050-10631C45C1B7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EB8638FA-3C21-4EF2-8B79-93883F05F943 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C5795EE3-DCA7-4341-ADE3-E367541AC51C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F47195F0-4627-4796-99CE-C13BDBDA412D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BD070B94-D7D4-469E-9306-549C74DBA4B6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7ABED254-B1FF-40D2-B41E-FBBB4F3B4EB7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8E093D5B-9C79-466C-8232-D116F8D655BD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CE3EBE0A-AB65-4634-8964-5BF42A20F26F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D1F62B2B-DBE0-4E13-B6D7-766BA14C86BA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2C604211-A557-4AE9-97BB-FA7017B80167 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6775ED5E-7066-45DD-B75F-4D98FCAED2A9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0B85A7D5-5178-4365-B442-7CD03EC3E738 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5B9C7255-F127-4E8D-901A-0EEC62F69A14 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C33B1A55-E976-428A-845D-E0163B579765 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8A051829-C8ED-4828-BA97-E7802112F842 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 71614917-E9FA-42BB-AD0F-C4150B3E7746 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 29054BD7-00D7-49DC-BAD6-24B79062E29C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5409499F-B67D-489E-A315-E678C50B2140 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 328231C8-9AF6-4B0D-9063-ACA864B74A75 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CEDDACF9-8685-4633-88F6-F40579ADCED3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 33BC57DA-7A5F-43F0-A08A-E423FFEC851D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A85BF51C-8929-4C89-8195-6B5C76A9ABDE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C6619064-A134-4B87-A6E5-21E35995DC6C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 286D1ABF-7774-41A3-8B64-92B325FD88A0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 13033C64-C109-4A6C-84E3-8E8C342513F1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 91325433-241C-4DA0-A584-6AE3460F06D0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 653EC667-E5D7-4705-8345-B76E2213A939 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B9204738-5693-4AE4-B826-EBE25C0E8F10 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 311BCCAD-FE8D-4993-AC29-739DC1A19E8C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5164112F-8CED-490F-8084-51F7D826BBDB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ED77AFC5-E22C-472E-B132-DA4E3841D906 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1504BB40-A567-46FF-8550-C87F85418EC9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3ECB55D7-BDD0-43F9-BCA6-9AAEA48F86FE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 01375E1F-11D9-4DE2-A892-91110254A7F2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DCC2FB95-1920-4BC1-8EE0-35CE0F423E83 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7FEB5B1F-2A91-414C-BD89-734B2D61D22E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F5122397-1ADB-4F7D-AB18-956F049DC3F1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2725EE1D-D445-408B-BE7B-CAB586449FB7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F5895430-3F2C-44CB-8E4D-7562C89FD32A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A4242578-33A9-4FCD-9356-3B0C348102C5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2B976A8C-8FA7-4B16-A94E-0EA061D5CEA8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 21CD5046-0699-4DDF-9636-2A36D15DFF2E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4392F00B-5DCE-4530-B4CA-B68F29615064 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 564B817D-37C6-4702-9118-5A7780B79DA2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 84D3CB6A-AE36-4FC5-B434-4E36B104BEEF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BC5945AC-3850-4196-B69A-232B2D89267A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B13CAA70-C0CF-4EC8-9962-3FFA5E957094 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8D4EC037-D7CD-4061-8988-D0F216A7496C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DFF6D5F4-ACE8-449D-80AF-AABCCAA4CA5C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7F47E4CF-9B8A-47C0-83B0-1C140AE7B892 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9499B33C-208D-499C-92DE-41F23DDF1E3A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ECE9ED88-4746-4B75-B753-AE192B5B9835 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0F382182-D369-417C-8174-2EDCA3938EBA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FB21CE68-00CB-451B-B230-30F9C1EF0365 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AE52865D-2590-471D-A7F4-AF1B11D5F596 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9ED7BAB8-F64A-4AF9-8357-38F56B982107 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 847FD2A9-6415-4B62-B36D-533B0AC09382 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0FFA803D-8D32-42C1-A714-531CC79387F7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6444E3FB-CB34-4EE6-B40C-6E0F383781CC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 71AB93A8-C5F4-4407-9FAC-3EB11869BC1C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CA20773F-6F07-47FD-8737-58FFCD47B8B1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1AC8B3C4-3E5C-42F1-AF74-FE1E8B474088 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EA53D32B-2E34-4654-9DC2-CC1BDE8DAF57 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F598A66E-2254-4BEF-8DC3-7460A4ADD403 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 80B60218-0282-45D9-AC72-07C0F61A0241 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AABF7FBA-6600-4E93-A372-1ADA6271D05C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 85716897-E928-43EE-8390-F03A99D075C0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6A652D12-D751-4C81-A349-7AD2C40658BC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 244C05A7-8CEA-4416-A1D0-5DD79C0400FE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0EA82C06-A0AF-48FB-BE0C-63CB38976ACA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0266ED83-E9C5-4314-B11A-5A46B3B4F511 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9068F425-83E4-4F16-BD81-FF9FE4DAE5FB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1B6CA134-3E1B-44FE-ADA7-12280D29C919 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D55EEE1A-6331-4801-8FE8-221B6E6E74F4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1338ACC2-B2CA-45F5-BE6A-7E9662511BF3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6EB21E58-9B8E-4FF2-8702-7E907AD1660A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FF303A99-4A79-4C02-8698-2A00A5F2B20C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AFA18DCF-9EC8-4EC5-8B96-4391568D649E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B71EE9E9-EC94-42CA-949E-1EC83AAF0C7D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E77C3F49-DD68-4E06-ABB7-333575CDD8D6 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-11-04 '-XMP-ph:RideName=Pontes da Ponte Rasa via Várzea do Carandiru e Baixo Cangaíba' -XMP-ph:RideDate=2025-11-04 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 64 — Pontes da Ponte Rasa via Várzea do Carandiru e Baixo Cangaíba' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 64' '-XMP-dc:Subject+=PH 64' '-XMP-ph:RideCodes+=PH 64' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 65 — 50 foto(s) ===
DEST='/Users/danlessa/pedais/2025-11-11 - PH 65 - Pelos Alpes do Jaraguá ao Subir Rio Pirituba e descer Rio Perus'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 9285CB82-67BC-4EB5-B201-29C47FAD8336 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C14BB9C3-F82D-465A-9828-775B1D067EB2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 11C3F3AC-E9A6-4763-B10B-BEDA298714E8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 93CB86F9-3AFA-4971-B742-EEDBCA4BEF81 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5D30A151-BA2E-43EC-9CCE-8FCA96F2610D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EF1D44A6-235A-4873-81BA-17A5398E53CF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 13C11EFF-03B4-421F-9A4C-9495D4E370B5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1FDF9C5C-523C-4FB4-A9FB-359B97F782B6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 95A2A313-0B2F-47B3-B836-3692DB361FB2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F5E3D1C2-FA58-4F5F-9200-3BB3FE8E051A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C5F7EAF2-72E8-4A97-8E43-CB3856FE8833 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7B744698-0251-4F0B-B2BF-3E1DD6719B7D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EA6F58C1-159C-4688-836C-8401573245C0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 99913D89-B408-45B4-AEAB-1C7BC4BF431B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 18309BA2-D75C-4F7C-87BF-936630D08F70 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 964FCB05-34A1-4777-A9D1-7BA2470D9756 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6CF909EE-B61B-4715-9326-63A36995F43F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BBB407B0-9101-4235-86D8-4FB1B8E8560D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 13302766-9C8B-4A33-AC7F-76829C12A0AB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 57C0AA2C-A589-4666-AD9E-EAC205E10FA3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CCDF772F-5045-498D-A86D-F742F8751AFB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AC16080A-18BC-4ABD-BA95-84EC43FD6358 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0196D14A-C254-4901-99D4-8010E7B1A03C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B0679F74-EC82-4E8E-A7A6-4A887C77AD48 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8D07127C-460A-49C8-A269-ACF0F1C9DE49 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1974F15D-BC5F-4233-AB8A-EE6B40AFEF95 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C8E81DEE-9C7D-44EC-A5D6-5312E89A1084 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E88C9AAC-C497-4255-B106-BAD45922714C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1B8852CC-4558-4B6F-A783-952AF49CD1B8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8821C3F3-17B5-4B23-A298-91A205AD1C42 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9ED254CA-07C9-4CEC-A86F-132DF09B1AE5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 89EA0788-C585-44C7-B717-99B66103DFF1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6327203B-436F-44C0-9FE1-962184F53302 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 32DCA9A3-785E-4DCF-AB78-2ABD54382F37 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8FFAF5D4-1F3A-4C72-B443-C1A469BFD448 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 11B54E24-13D5-4B0D-88CC-5F5769D33743 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DD08F200-D1CB-4D6B-A4AF-513C6584F611 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AABDD88A-4735-4588-A9A0-03A64E4C3FD8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7104E2E2-2DC7-4D81-84C9-B0325D8E464C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3B42B127-A68D-4088-A7F6-AE914D20336C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 97076680-7007-41FA-BC41-9D4FE49DAAED --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EE6E28CB-4E47-4FC7-91DE-EC509FFDB2F5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 12C6E4CE-4FB3-4D7D-A0C7-3C9AE87A8171 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BD996823-3ABA-4A95-AA6B-CB95461427A1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 91CE042B-4C3C-489F-ACD0-47B8767562F1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 99DD6B57-9EF5-4440-B8FB-06A55642BCC6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 20E11B37-0B72-4702-AC4A-CE222EE1A977 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F7C4D8B9-7489-4F05-B60F-D2BEA536FDD0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 08E06E7A-C6A0-4495-B687-02EC21B0D1E1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 955A4D4E-3F34-48C3-BBB0-842EEDF7355B --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-11-11 '-XMP-ph:RideName=Pelos Alpes do Jaraguá ao Subir Rio Pirituba e descer Rio Perus' -XMP-ph:RideDate=2025-11-11 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 65 — Pelos Alpes do Jaraguá ao Subir Rio Pirituba e descer Rio Perus' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 65' '-XMP-dc:Subject+=PH 65' '-XMP-ph:RideCodes+=PH 65' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 66 — 9 foto(s) ===
DEST='/Users/danlessa/pedais/2025-11-25 - PH 66 - Marcos das antigas rotas de SP (seus relevos e relevâncias)'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 0D3DF741-4661-450B-903D-9391625842A4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 57D7CA09-EC36-4729-B419-790F623941C2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DFD660FF-573A-475A-9501-415B76966B80 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A5595DA7-90BD-4CC2-AB0E-67751E82A101 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 50D68FBB-4C50-43FE-AF2E-8E1E9B9811A7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3D2301D5-5975-49E2-A5B8-144AB91F769F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0CE00662-0481-4036-A0D5-D32A1B58F358 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3E600C71-CE84-46FD-B7EF-4D8C952834DD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9F3A1913-6919-495D-8BB4-A66831D8B4D3 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-11-25 '-XMP-ph:RideName=Marcos das antigas rotas de SP (seus relevos e relevâncias)' -XMP-ph:RideDate=2025-11-25 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 66 — Marcos das antigas rotas de SP (seus relevos e relevâncias)' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 66' '-XMP-dc:Subject+=PH 66' '-XMP-ph:RideCodes+=PH 66' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 67 — 49 foto(s) ===
DEST='/Users/danlessa/pedais/2025-11-30 - PH 67 - Recosturando Tietê e Paraíba do Sul'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 8687A04A-32FB-4435-9412-8DCEAF4ABB7D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C8419532-1EDD-41C6-BB69-8E0ACB8D7723 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 05A67344-C097-4E77-B365-CB88248D03C8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 01BA082B-42C1-4685-AB40-EF57A8F8BB1C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EFE5D1E3-026B-40B3-ADA4-DB8C5572E9F3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1F595E6E-9CA9-4488-9D46-F0FE0653A958 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 844E4B89-8088-4E44-BE50-20AA2631D3EF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 59E252EF-B80C-419F-B09B-AA67B32298D8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 483230B8-6E76-4842-A948-EB149F0B77E9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 25A1E9A2-55C9-438C-86D3-D2AD436897CF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 45F82888-D882-4F78-84A3-6B98077F4F23 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B0AC0A64-27CA-4408-9B05-E9B309595C45 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9A085A65-7DBA-40E9-91EC-ADF7652A43A8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6FE5839E-F66B-4596-9BB4-D14E0088F608 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 164E09DD-C37A-4D70-A91B-E91081054F6F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 351CF090-6CB4-4AA6-A49C-B72DD06D2D0D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BBA30914-D42D-45BB-A022-28C9C95B31C9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7DA78127-82CB-40E4-ACC3-2CAD5AF5E313 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 92471073-EA1A-4BD3-BD99-ABCA9DFA8731 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1CA57CEE-B1DF-42CC-8266-031DBB9E0E9C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3F36D4F4-B69C-4B3A-9297-9E177CD34606 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 427273E4-E3F6-474A-A634-8F4059B73976 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D35841CF-DD35-49C1-9338-B2B47994E900 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FD252D28-8397-482D-811C-A1B649A08914 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CE94D732-5093-4316-9777-428CB8BCC1F6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5BD9ED0B-9A8C-4017-98BA-3BC46C057D80 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 27C305E0-819B-4FE9-9F0C-4598042D1187 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7C4A471C-6CC5-45AD-BEEE-85953E328343 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4211C3F4-60FB-49F4-9465-31E70CBD4CD0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 48DCCBD3-5234-4BB5-9B7F-B5C148812204 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BB7DEEEB-E176-417C-B060-B8056062973F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4CACB958-DF50-4CA4-B20E-DA4B03720247 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 30DC27D4-BDBF-468D-B647-6FECA17FD8B3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F30CBAAA-7C5C-4A6D-9EA8-E3B46DB4BAD4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 89C3BE31-4228-4264-A203-D9B81B030023 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8F33F614-599C-4083-8DD0-4FD2C02CE01F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 060116DD-62B2-4AD1-8D9D-E221F8B42128 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EA1D5172-9E0C-49CA-804D-D07241F4AB2F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BA3E1663-C47C-442A-9316-CBA02A89C971 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F9E5B2A9-FC99-4E8E-BC72-3478338B3592 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 22547518-5B0B-4586-B1F5-247FAED29DF2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8320354A-65EA-4FED-B95E-EB2C25BFFCE7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AC09A31E-5CEC-4203-A71C-60015108DE05 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 69B5A04F-6B39-4891-8006-C319E3C5622B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 398AE2A2-1866-48A7-BE3F-A1E789BB1792 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B70471F3-7115-4BFB-8355-5A1E72A29602 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 44CF5B2A-E057-48E0-81F6-9FC95371ACDF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 95C4B1EF-3633-41B0-AC91-5E0223ED38B7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 92247D69-5C73-4D64-8FAD-4E648A3C73A3 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-11-30 '-XMP-ph:RideName=Recosturando Tietê e Paraíba do Sul' -XMP-ph:RideDate=2025-11-30 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 67 — Recosturando Tietê e Paraíba do Sul' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 67' '-XMP-dc:Subject+=PH 67' '-XMP-ph:RideCodes+=PH 67' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 68 — 2 foto(s) ===
DEST='/Users/danlessa/pedais/2025-12-03 - PH 68 - Contornando Capão do Embira e Tatuapé pela Crista de Sapopemba e Vila'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 824F3536-35F4-474E-85EA-D13BA431FF61 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8A0D29FD-FA5F-4386-9E6A-B696252D9661 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-12-03 '-XMP-ph:RideName=Contornando Capão do Embira e Tatuapé pela Crista de Sapopemba e Vila Formosa' -XMP-ph:RideDate=2025-12-03 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 68 — Contornando Capão do Embira e Tatuapé pela Crista de Sapopemba e Vila Formosa' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 68' '-XMP-dc:Subject+=PH 68' '-XMP-ph:RideCodes+=PH 68' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 69 — 50 foto(s) ===
DEST='/Users/danlessa/pedais/2025-12-10 - PH 69 - Tiburtino e córrego das corujas'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 994B1596-9892-44B0-8320-C3C7B91B5C6B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 667897D8-83E3-47B3-8337-B5AA30BA16E2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1EB0934C-6D87-43E2-8286-16B3E9539932 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 62599EAE-952F-444A-88EA-8C287BCD07D0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6E3B202D-DAF0-489A-A98C-C10DB046E370 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 69EA4A92-FF53-44B2-80F1-0F4E13B223D9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5B59852C-4CA2-4793-9B61-8A105A81BF1D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6F13C140-9CB3-48F2-B525-DAABE9D1D47D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F20C7CB2-793D-4F50-B552-809F59028122 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D47971CD-2A14-4089-8576-87E671058A1F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BBD908FA-046C-4786-81BC-EF931239E4EC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CAD0BFE2-0004-467E-91A6-3A98A3E75030 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B91CA37C-A97E-4B0D-8D99-79D3EBBE2C1D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7EDB08AD-EAC0-46DA-AC1F-FC17D9802277 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9D377CA7-9267-4953-B03B-7C7FB3AE6F1B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 087C32F3-2B3F-492C-AB7C-F00F91E6CAAD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 698414BE-DA47-4BB2-ABF6-AFFFE32494BF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2B53D5E1-516E-43E6-AFB9-E0D4A1740772 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C4EFD172-5197-4E4F-BF35-6C9F0283329B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9B12A090-B00E-498C-8519-930EFBD73EE8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4B791F7F-4B15-438E-99DA-CEA15A545A11 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 67CCBFB2-9DA5-4114-B875-86E0C84A5E80 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5ACEDC99-CC53-42C5-A040-67D7D3D6FD90 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 846678F2-E196-4324-8803-191364ACCBA8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3437CC24-1F9C-4CFB-8EC8-805F9EE1B5B4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6CA7647F-B4A8-4BAE-A844-4BF7877EE158 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 904FD676-E4BA-42F4-8C9D-6B9A24AA3181 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 29DFFCA5-6D1D-4034-83FE-78DD022F32EB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1ACC41FD-E272-4C3C-AA94-E8CAE1C65E6C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 995C7FBC-70F3-46CB-84E5-5B0C41E506A5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 16023866-B02B-475A-B111-A5B98A294D6D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4C785A72-CD14-44EB-8A5A-7390164394E6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A9F261CB-A6A3-4F90-A5CE-057731FA8BA6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 21872A15-228E-4C92-8EAF-CF7C60F1E2E1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3386F8FE-6FD1-4C9A-99D9-B707BE4C00E2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4EEE46ED-0323-46F3-A18B-1AFC290E85D2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EFD5132C-CFEA-47E3-894A-187ABB753D40 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 94A2627F-7765-4BED-96B7-F2A9F416DAE3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B23C8C7B-3169-4DC1-83D3-22A06A40ED36 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 51CD11B1-9403-4378-AA5F-D02510740069 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C496A7EA-5AE4-493B-83AF-7987AEA5FDA2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CBDC4774-9E3B-4262-81FF-5413C9695C97 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 60276F72-84C0-414E-A4D0-A4F5CB83859B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FBDAA57D-57F5-4C2B-AF3D-AED3DA7508AF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3F16E61D-6E02-4B3E-A13A-53625A90060E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7959EFD6-B531-4EB4-ACC5-24E44BC51B65 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4CFC438B-0297-4F47-8E20-A1BD5595B2A3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 77A71F64-BFC4-4E4A-B117-0297A18A8FAE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C7899F6F-38A3-4855-A729-1DF0AE83C531 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9A687BD1-36E3-47C6-8351-9C2DCBF4FE4B --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-12-10 '-XMP-ph:RideName=Tiburtino e córrego das corujas' -XMP-ph:RideDate=2025-12-10 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 69 — Tiburtino e córrego das corujas' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 69' '-XMP-dc:Subject+=PH 69' '-XMP-ph:RideCodes+=PH 69' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 70 — 52 foto(s) ===
DEST='/Users/danlessa/pedais/2025-12-17 - PH 70 - Cabeçeiras do Ipiranga ou Desmorrodouro do Caaguaçu'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid F3C2DFF8-19FD-4642-A6EA-67268930369C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 74C70F09-4AD8-4CC8-AA64-04530A5B1925 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 06A8A295-5F73-468C-A2E6-E18286DF9264 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B9B50DA2-56A5-4456-A9C1-90214CEA2710 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E5D8B27B-1DB3-4831-913B-99077D508E4E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4E94B410-0F90-44F4-A93B-1F4B0F0CF1E5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A83F4DB8-6C78-42C8-A764-48ED240C7B38 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0A51B372-E143-4278-BD14-BA3A30E6A608 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2771F07B-7E12-4708-A429-2754FBF0538E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D3A6A630-CEF9-4003-9587-41C8ABE1FEDF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5DEB2CD2-B452-43CA-80E3-9E59F3304474 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5FDA1855-BFA9-48DB-8297-D42BD8CD96DE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1887096E-3DA1-4CA7-B7B1-A2E23BF701B4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DF7A8F0F-CDA0-499C-AFDD-15F06A6DBF62 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 85F2AD63-B52B-4FF7-B6FF-71D8CAC75731 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B020F76C-76EA-43F0-BE0A-4EB0503D81B2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 18736933-F555-46B4-8E2A-F51AD9F13864 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EFBE9475-E792-4A22-A9B9-EBDD362A52AE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0D2BD0F0-BC63-4E49-81C3-BC9F01077B9C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 54CB93EB-1D92-427D-B7DC-D31317900A57 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9A3E2D31-25E4-4B16-BD61-03FCF573CCCE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B1AA89C3-AC2F-446B-9818-54B0F8CE59B1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FC2FA58B-B6D6-4E77-A2AC-E7AA5E96E920 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9E850DE4-EC1A-4285-9989-55C27FAFC5ED --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FB2569FD-F431-44C0-A8B8-247DFD2BA1FD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 64CE6620-340A-431F-A610-86CB2283CFEF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E79B3B25-9C5D-427D-A358-2AF22CA32F01 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A9BCBF23-C9F9-43CC-BB8B-E804440F9560 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7BE6A04C-B7EF-4790-A682-4DD2C2C366F7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0A8466C8-281D-44D2-AD6C-C8C6EBC36439 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7E7A3C13-C015-4E15-A18A-53025BBA5BF1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1536F12F-59BA-4476-89C3-0FE506710B66 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3661C064-837B-4763-A9A0-4E01F75836DE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 45599174-5C7B-4E15-84EB-89F3804456FD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D8ACD763-FA83-4E7C-88AC-FACDDD7E4F1F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8176D681-8256-4175-B2A3-8535FBA8499F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FC66AA19-B939-45E7-9E35-7D13A1C4DFFC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 087586BF-224B-4B28-AEA6-F97FF9D5BA2F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7200E38B-26B3-4536-97E3-56FE64C74987 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 99E7B36A-BE9B-47AB-9827-B548057A9AC3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BB24B3C9-544F-4EF4-BCEA-A2CD35B853C2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E89D5C55-9B92-4484-94FA-C6B26A9993C5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2DCD577A-A773-47AB-8D56-3A75D51EC17D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 68827648-57DC-44F0-A5AF-D7EA37574DC5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 929E74BE-09C1-4DFB-904E-647DD34F6EA0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0ED3913C-B246-4B05-A9E9-910FAAEAF379 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C30D31FF-D72C-4894-93BA-69B4CA0315DF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 87B84134-4005-4E11-9BCC-83313150DCCA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 30FC973C-77E8-4730-9FAF-329841134F8E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0FE89981-62F4-46B0-ABBF-FD1871AFA1BE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 52450687-01D5-4115-93F3-2504C4545D7D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DA8F843E-3396-4600-B5BD-7017F853A57D --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-12-17 '-XMP-ph:RideName=Cabeçeiras do Ipiranga ou Desmorrodouro do Caaguaçu' -XMP-ph:RideDate=2025-12-17 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 70 — Cabeçeiras do Ipiranga ou Desmorrodouro do Caaguaçu' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 70' '-XMP-dc:Subject+=PH 70' '-XMP-ph:RideCodes+=PH 70' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 71 — 51 foto(s) ===
DEST='/Users/danlessa/pedais/2025-12-23 - PH 71 - Bonde, Pedra e Cachoeira'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 5AEE7380-9BFC-44E3-9DAE-E053C9B99E34 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E3E5B507-C17E-46ED-8998-3403187F7DEA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0ACCDA20-8A62-4416-90B4-AD62936E3F9E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 580B6E51-B638-478F-A6A7-85A3CB3856F4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7DD963B3-CE0C-40D9-9ADE-F7752D7642B2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EF8F4ADA-D12F-4535-8B72-3FBAE9769BE0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 27914930-0AE8-4D88-8F1D-34123E325479 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C4527D16-DCB3-4C3A-B322-3690D79EE63C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DF64FF16-CA06-423D-8528-240FDB3411E7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 58257562-A130-4CDD-AEB6-9B1BD47CA094 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CA4F3C49-F236-4982-9BFB-9EFE019F26F8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 28DB8956-569A-4117-8797-2EEF321DA084 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 01311778-BAD8-4675-AA80-890BDCD640E8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7922DAE1-9053-4340-A167-8D0EEF7E3918 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C2E9F295-72AF-4095-BD45-F5BC40329327 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F296FB24-0377-4D3E-9F9D-AD8F87A87B22 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5ED455AD-0C7F-4EE3-8132-7B36705BEBE2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DCEB96DA-812C-4A28-8006-5C29B2151C16 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A6C93B9B-0D73-4744-89C9-53818E185BC2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 29D2A779-4579-42AA-AF6A-AD3F853BD981 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3B7D3EC0-7EFC-4A43-842E-2AD41C355620 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 49D75F76-5E4E-4D8B-940F-12FEE8AB5925 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 841C0C86-BBBE-44C0-BB6A-0CE1AA014338 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2C6ECF35-0593-44C2-BCA0-4BD3E752839E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 32E399B6-BB54-46AD-AEA9-C3FC51C505D3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BED8CAC9-24B6-4994-B6A6-07394B93F3E7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 68262EE6-E39A-45BD-BC62-D54DFED14814 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BAC00CF7-8CE2-430E-9141-3783A8903B98 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FC7CC0B0-533D-4536-985A-96885D743D12 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D34D3036-44DB-4758-A88C-14E9B5AC1F51 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8A1EBC2C-CAB9-4816-9219-15D1C6C4BEE8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C1682EA6-B71B-4871-831A-7B34FD4CA3B8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AA3A8C38-36B3-4E92-8922-899023B04DCE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D522492D-D66C-40DD-89D1-C4DF6FB235C1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F00F9B26-D83F-4C57-AAF0-68497D7FDDA0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 90170646-B233-4670-A43C-B3655F9755BC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A5E302C4-536D-418D-8CAE-315297B90FF7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8CB455C8-D499-4BD1-83ED-4CF53501C196 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A6468756-E6E0-4C9D-9F05-72C25BFFD880 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 477B6926-337A-42B7-B5D9-3B9A179D71BD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 87F95A5A-1193-4A1A-9E62-61D57864CCFE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 14FA76D9-1DDE-410E-A867-5E6395FE549D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C8F544A0-9A36-4515-B954-5775303F2A01 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CDE80AED-FAEE-4EDB-BFD1-80E5F6BD9939 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F6F829D7-1A53-4B16-AD33-7FF191689032 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CC466780-DD19-4E31-B32E-A5E4EE479E75 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BE2E29A9-4CB0-45A1-91E0-0A92E3752939 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4D2D3A5F-F532-4026-8C44-F212C114F4B4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D5C39980-7157-4A57-9364-E0CBC4D536CB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 81D0A53F-A9BA-47D9-8BBB-AF5B210894D7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 930226FD-7AD2-4C79-8F3A-822CB32358A9 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-12-23 '-XMP-ph:RideName=Bonde, Pedra e Cachoeira' -XMP-ph:RideDate=2025-12-23 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 71 — Bonde, Pedra e Cachoeira' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 71' '-XMP-dc:Subject+=PH 71' '-XMP-ph:RideCodes+=PH 71' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 73 — 39 foto(s) ===
DEST='/Users/danlessa/pedais/2026-01-14 - PH 73 - Contornando Carandiru e Paciência'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid B96C626B-50C4-4D3B-A6F8-8F9408B3ACD0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7E41FD07-CB6A-4A74-BB6C-ED3DC846F87A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BA8A3F4C-10E2-4986-A3E8-798976AE9B8E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 50431CD1-3A96-48C0-BDD5-CE8A625C657E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 942900B6-7D98-428A-B6F6-5C7A6EA943A1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E3496B3A-462A-4527-9000-9A7DE4440C32 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F1A1CF28-39CC-4D09-B3EA-EE95F26CD34D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8DDB75A0-60AF-4DD9-B284-CA0B4F2ABAA1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5232A32F-C709-4CAA-9863-7C5CD93A773E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BE02BDA0-26D9-42BD-8249-4E230E189854 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 96808F7D-93E6-40C7-818D-48983F4A2AC5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BD9AD6D6-6C73-4682-B23B-CFAA377EA399 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DC6F20C2-44E3-4D45-BECE-8BA6581EE89B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2A973ADF-8ED6-4611-8468-1F8EE9940266 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8044192C-6BF6-4725-9E99-DEB4A80A251C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7FBA7C72-3F5A-4FA1-AB44-5EAA2B35EE9B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BE8BBEB5-94E1-4B5E-94FD-B49CD4DF2A0D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ACA19271-9338-4289-B960-EEA4CB16FE8D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B7F6368C-2642-43AA-8609-626B488BB5D8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EC65BC5C-A7E9-4C8D-9EB4-6D923C1429E1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2112F9C0-A6B8-4752-84A8-00067218C312 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 372CDFE3-1E9A-43F6-939B-06A95B0F31EC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3681DCEA-5004-46E9-B297-5CCA56C2463E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 50D8D6C2-5C34-4E65-8C0C-85D63AF7329C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 96A11C9A-FA40-44A7-9DBE-EDF343EB9878 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5671B645-23DF-4D2B-B6E5-931766D0C038 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 56D3D46F-7739-4055-961E-AD038672A577 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0991F3EE-42D2-48A9-AFCA-C7ED1CB311B0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6028AC5A-4902-4A26-9E09-D7C4EB78F3C6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 70C3F7F3-7E24-41F4-B830-D8A5311A1C02 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 900CA621-89D1-49F9-9E2B-D35A65EA7498 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6445CA91-8028-449A-9174-6FAF33EFCCAE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ADDD698E-CE7E-44AD-B1AA-FF9E36347428 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6805B761-4D0F-4B4A-97D7-5908B145B0D6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FBFECD9E-F2EE-4C61-9096-E6F6D9E8A4DA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AF789F77-31DB-4A1F-BB2B-E06762F6BB90 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 110C0EEF-E6A8-43CD-991F-FEBFD66CD32D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F4E4234B-2DC9-4DB0-844B-9878750DA1B5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C94A8AB5-E852-4E8A-9FE6-297D8EBF43E7 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2026-01-14 '-XMP-ph:RideName=Contornando Carandiru e Paciência' -XMP-ph:RideDate=2026-01-14 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 73 — Contornando Carandiru e Paciência' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 73' '-XMP-dc:Subject+=PH 73' '-XMP-ph:RideCodes+=PH 73' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 74 — 7 foto(s) ===
DEST='/Users/danlessa/pedais/2026-01-21 - PH 74 - Pontes do Itororó'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 386D9C56-2B81-433D-BA43-2F9DE4C7391B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 397D58E5-0B70-4E9C-BC21-5B4534BFBF11 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 564D0DFF-BFB3-49F8-90BE-94DACCB0C437 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4A8479DD-2D4D-4F36-8839-632204EB84E8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BC321618-1E2A-45B6-8694-6485279B1292 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 624C266F-E282-4961-BAEA-15455C952289 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E34B393F-58BD-43FD-8838-10BE30444446 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2026-01-21 '-XMP-ph:RideName=Pontes do Itororó' -XMP-ph:RideDate=2026-01-21 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 74 — Pontes do Itororó' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 74' '-XMP-dc:Subject+=PH 74' '-XMP-ph:RideCodes+=PH 74' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 75 — 58 foto(s) ===
DEST='/Users/danlessa/pedais/2026-01-28 - PH 75 - Circundar Canindé pelas Águas do Moinho e Biquinha'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 254C1728-66E5-4490-A76A-571F40CEE6AF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3227CF2F-0285-455E-B668-2FFDE21026B9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C867DFA9-E236-498A-A973-34826E33CAA4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1019C770-A6AB-4F05-A6CC-70A90922EC5D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 27767151-E1A8-4405-9F34-738AE1C8A02D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 25D76A8E-91D4-44F7-B03B-E58CA8D5F1BF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 55B49B8E-EF58-4E9D-837A-948C5031C80B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 206DBE38-0509-40EE-83B5-E6FD24A1A04E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AB01882C-C19E-4545-A812-D513FC91164D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AADEBF4E-B508-4FD9-B65B-FCCA3434BD39 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2D21C6CD-1EBD-485C-9EBD-015B01933E38 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 58A0E601-68ED-44FE-A04C-D516E4498F73 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 728F6C21-9259-471A-8D85-DBEC144635B9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9475048A-8692-46F4-9515-A1EC7B75F7BC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 88D4CCEC-2A93-4CD7-8F17-40B5E17C57D8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EC7B24F3-A7B9-4AC3-B783-7A052E2E12B8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 78433370-244E-432B-B549-2CECD0AAF8E0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B0B00533-B3F2-4F44-8448-D7F684C6A48C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BEDB1B28-43FE-499F-8BED-F2B4DA6EDAE0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A1A61908-EC0E-4714-96EA-EB2D4734D92A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EB179F11-2AD0-468B-8FA7-9CE66CCD7E1D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0DE1CEA3-BAF9-4186-9C46-E502DF5B5581 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AF227AC0-3C64-4B81-9DE8-A09FBA89BEB1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 23E657E2-3622-47F1-BCD9-E659DF778318 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9D4D2776-D91B-4903-82A5-67C48BB6330D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EB7AFD15-6BDF-44DC-9FC2-F85E35A4F107 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9F47A5FC-BFFF-4ADA-8B7B-DECFC60B36B5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7C48A21D-0BF0-470B-B4CA-056880518AF8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5C6D3C07-08DB-4BDB-BA4D-1E7E7DF9047B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3734ABF1-5614-4A2C-886B-F1A96674B1A7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 42346FB1-7B4C-43D0-8DA8-3A702676FB4E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9A73B1DB-DA2F-42E9-B8FC-D68C7A957835 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A970B484-AEA0-442A-94CE-5764864D3D3C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9260EC06-BD76-4674-9B1D-AECF54E81E88 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8BD01C01-C9EC-4DB2-A45E-B63E650080AD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D51DE61E-3838-4C06-97E4-21156E5E039E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5BF3A67C-ED67-4F67-BF71-B38A618B32B7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7B934E60-20B2-4017-847E-C0411C33B613 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5F56CFE0-2D6E-4372-A269-23751770527C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 99C09983-45F9-49B8-A48A-60AD5D84B35E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 539B4A95-7035-43BD-A2A0-B0B90B99C4A4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C9D91071-2956-4B3E-94B9-C3ACCB8D7160 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F75E2A7C-3402-4EF4-AC60-CEF5164F33B3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 55F53423-2123-4582-A0BD-E47D73D16AA5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 97B9F2F7-1288-4E46-9611-9A83186D4269 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B1190F92-55AD-4AAD-91D4-2F091411B9DD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 277E420A-967E-4F99-9B2A-27E59A5485B7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FF617359-4A22-4D95-9B4C-DDC1B55BF265 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6A4CF262-A9A5-466C-91E4-D894C2ED54B1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 17F77FDE-C5DC-406E-AF67-737CB382F795 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 25701A9D-297D-458C-8D2E-5B671115CED3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9615B2A8-9C17-4A54-9E49-060CF28C751B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 976098BA-F78A-4B06-B1CF-2FADEE2AB498 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4906DCBB-0875-4FA2-9951-D318D2487330 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CBC77C37-6657-4617-882E-87B689DE8D41 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 57FDBFB2-8A4A-485B-A000-9C659C347FA1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2D1935F3-D76E-4BA3-A0A6-1EA95800C4DA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 11CD839F-67BA-407E-94F5-C710A96950B4 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2026-01-28 '-XMP-ph:RideName=Circundar Canindé pelas Águas do Moinho e Biquinha' -XMP-ph:RideDate=2026-01-28 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 75 — Circundar Canindé pelas Águas do Moinho e Biquinha' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 75' '-XMP-dc:Subject+=PH 75' '-XMP-ph:RideCodes+=PH 75' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === SESC Consolação — 2 foto(s) ===
DEST='/Users/danlessa/pedais/2026-02-01 - SESC Consolação'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid E0044617-E7F6-4337-9981-FDAA2084C71B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B76845D4-444A-4B01-8876-574CB6B7C033 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2026-02-01 '-XMP-ph:RideName=SESC Consolação' -XMP-ph:RideDate=2026-02-01 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=SESC Consolação' '-XMP-dc:Subject+=Pedal Hidrográfico' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 78 — 33 foto(s) ===
DEST='/Users/danlessa/pedais/2026-02-11 - PH 78 - Lavapés, Saracura e Banana- Três Constelações da origem do Carnaval P'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 768F24F9-828B-4FA2-8E8A-ECB7B6AC1824 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2DC28462-B84D-486C-B54C-29C313AC2DF8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1D91AF97-E046-41F5-ABFE-847EE0B1ED27 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8AD5C0B9-801B-4F54-BED6-D8586E261E79 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E5DFE996-3753-42A8-A0E9-70803CBF5C1F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CC983F51-2C71-44A0-99C4-66CF55189AEC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9E97FAA4-7C57-4DE0-89AD-49372618CB4E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DC395A35-65B6-443B-984A-FA42C6657A59 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5CCFFFCD-30A0-4192-A762-261F102F688E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 048F7B43-CF47-47AB-9DC7-572EADDC6A29 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 889E5E56-891E-45F9-918B-EA85F8A8EBFE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 44C4C194-B0A6-4ACA-B8A1-77261FA303DC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E2416AD9-670B-4AA9-A3EC-99181B849EF5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6132224D-CF8E-4C3B-9AF6-5A6F28E4A23C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B5717437-B386-4378-9893-7887DACB8802 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 01539743-FD26-4FCE-9698-521C6F170B90 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6213FA14-1AD8-4596-A581-10B5C7E77465 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 45A2BE8A-BE9F-43CF-84EE-21BBAB8738DC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 177702D4-7173-4857-A77F-2D7B2F760E1F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B75FE6BD-6F42-4214-A930-65DC45F03C6F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C978B3B2-C2B0-4D16-95EF-41C612E7F523 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 033520F9-7E95-4DEC-8BD7-70155F59E5E3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 83F71157-8B5D-4788-B30B-A8EDDC776BFB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 05AFEDA4-1FDC-466F-8E56-84261F79E37B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6EB5ECBB-C027-4249-BDC2-88E6D7EF6B96 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 88DFF27D-D296-42E5-A1D7-88B08E641704 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A4358474-1F60-4C5C-B18B-8671F7882A95 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3BAB62FF-DE5B-4894-8E9B-9DAAD586E2C2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DB0702E9-A210-4EDC-B9CA-A3C258CA09F3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8C77B41C-CCC6-4EF3-9FF4-62B3907CA586 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B2C671A4-A3B9-4B21-BC7D-B498F0D824A5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 80146849-F0CD-4046-9C25-BAE7D6D9D91A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9EF1DC10-EFEE-48A7-AE24-1055EF3381BD --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2026-02-11 '-XMP-ph:RideName=Lavapés, Saracura e Banana: Três Constelações da origem do Carnaval Paulista' -XMP-ph:RideDate=2026-02-11 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 78 — Lavapés, Saracura e Banana: Três Constelações da origem do Carnaval Paulista' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 78' '-XMP-dc:Subject+=PH 78' '-XMP-ph:RideCodes+=PH 78' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 81 — 64 foto(s) ===
DEST='/Users/danlessa/pedais/2026-02-24 - PH 81 - Planalto de Taipas e os Cânions da Brasilândia'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid CB9BE623-E90D-41CD-A4AF-3DC9058CF121 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1AE85B64-F30F-44E2-A977-27943DB9F9D9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ABDB2ED7-9CBF-44D8-B939-FE9BE3F157EF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EDF83776-E839-4148-8B5A-977CEA9B5756 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 15AC3519-2C37-419F-A07C-D49F7E0D4660 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 81A11B59-412C-4C4C-9573-C3FD05B43002 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4DD07FE8-833A-4738-B7C2-DED6E65CE577 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4320F933-5EC0-4973-AEA8-98CDF1884AB6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 549847ED-A174-4585-B268-9616535572D3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 67BEFBBB-FFDA-4B20-8E62-99415AE07DEF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6465332D-5A2F-4455-A904-E5843F626583 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 283724F4-FBFE-43FE-B333-FF360424070A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C2EC1EE3-59CC-4A84-81DE-2EBA4CD146A4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 19BC5728-E77C-4042-8E2C-9045408D1367 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 486B72B5-FFB7-4C2E-A03B-60CB6981CE03 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DE4E76E7-5E87-4E8A-83F7-F5BF30035265 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A6095938-131D-46DD-BB74-B41F467152F8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A6C1CA1D-631D-4895-88BE-7BB510F2B604 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6BE05231-B9AA-4DDB-9252-1B638A29098A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 97F90866-09D9-4CE1-9123-18FE8E37DCE7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CA39E547-E63F-49BC-B7E9-AB7047D974A7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 584FB268-E492-413C-B332-81CE5A89563A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C8A1E1BA-FC17-468C-8917-BBD5D45B3F51 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 36B1464E-BE1A-4F36-9A14-4CD95B88B1D7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 964055A5-21F6-44C2-A454-F51FE0AF3A5B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5970B725-5E9D-4FFA-8CB3-14548C5C2790 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C59EF32A-55C4-4724-A811-C17512DAFE2B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BA91AD73-4AEB-4326-A612-40D01159D359 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4FCEB5B0-9B04-49EC-A546-298747720327 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C8353B01-639E-4B02-9B3B-17318952DBF5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 137117ED-C8E8-43B5-A875-4E354D0064EA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E8FFB6EE-7A9D-4DF3-8062-BFFEF47AA657 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 69BD4B54-4AF6-4A86-BBC6-C9A8E4AB668B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 57BCB848-C5D0-4E3D-BCF7-41E82B5E53C4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1F32D819-A4F0-4544-911D-3B43398AE1A3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1883CB77-F207-4964-8B44-4796A54463C0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 348A097B-AC10-4EF3-8571-78D59C6529C2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B2A7F80D-7A51-4CCE-84C8-5AD020FF7206 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CE17023F-4D2E-4AFA-9E90-714F1BF16931 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4547F8A3-F3F5-49C1-BB66-F99DC7C1B767 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 84815C60-B395-4FF8-9F13-FD517EE8D053 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 010517AE-5D54-41DE-B5D6-7E8C6878F4F1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CC33C285-1221-482A-817E-6A27A298B5D4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 585064D7-A595-4397-8A65-6E8DC49ACE37 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 66F349EA-A9BB-44BA-A3D7-E68DFC4D7D06 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5AFAE317-9790-4EE1-96A7-36BD509A2874 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7B6BD140-8F73-4D29-A4F2-DDD78CDF08AF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 59DFAE2C-CE49-481C-8BEA-34485F8630D6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 16D08F49-2D2D-4874-A4DB-A794588877E3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 22D7CE45-E8DB-42AE-AE3D-84EEF0AF9359 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1180D04B-5686-410A-8F28-37EA0B92B538 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 905D7BBB-B54B-4696-94B0-D2C846DBF586 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F0B7076E-5EE1-4FF6-9FA7-5B95AA35A365 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 95A0256E-BE67-49B5-98AD-53AE4F93943D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 742AA987-81B2-46F4-9CED-F8FC065FBD9E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D4F66B4E-EA54-4E19-9171-EBC6457348AB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 202AB37D-9E3F-4422-93D6-850CA4FE469E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F97070AB-EC19-470C-852A-ADE72C4DF4DF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3826461D-5E00-4F59-BFEE-7A1B0DD189DE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E5D1EC02-0288-466A-81DC-6F5D0F9836F1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 16448064-405A-4364-AC98-F2F54AAC685B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8514C0B9-384B-4E96-B131-682CDE3DDD95 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C95B447D-3F74-42E6-9745-E7C0FA0D7ABB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 21FA0A4D-4381-42B0-8CD5-62D38C6C52DE --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2026-02-24 '-XMP-ph:RideName=Planalto de Taipas e os Cânions da Brasilândia' -XMP-ph:RideDate=2026-02-24 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 81 — Planalto de Taipas e os Cânions da Brasilândia' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 81' '-XMP-dc:Subject+=PH 81' '-XMP-ph:RideCodes+=PH 81' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 82 — 34 foto(s) ===
DEST='/Users/danlessa/pedais/2026-03-04 - PH 82 - Colina da Matilde e Riacho dos Machados'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 890B27E4-AE1A-49CE-BCA7-BCACCC6E84B3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E6DE40A7-92AE-4BA8-9A9B-29D0AA72E166 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C871A4E3-D209-4803-BAF0-864AB87E8AB1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4AE56218-0585-4386-99A2-478AA29C3FF9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2507E19D-FF22-440C-8117-A40BFB85A6D9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A6337D41-C715-4622-A4C8-EF05ED307176 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 87DA3E73-486D-4A28-963C-C24D1E1CEA7A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 63CDF25B-86E8-4A5C-99D8-87917CA6122F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C83C5166-78D1-446F-88BB-1CE406C9A34F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 55A9DE2F-2DC6-41D1-8B97-BB9E05942D81 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 59A08F41-4832-4CBF-B87E-9A8CF7B20409 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0F77B454-CAAA-454E-81FE-8D142EDBEAD2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B50EFE17-E1A8-4F57-9A6E-374335597229 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9D4FEA52-8421-41C9-BC60-67CF04773899 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 86B70C40-FFC6-4BF0-A029-D752C0AB13CF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 19C555DF-2190-4A7E-9C23-86DC39426BED --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 76A9D71B-15DA-4364-B2C5-8FB4EA793F7F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6160B994-8BF2-4EA2-93B2-AB20B0CB65EE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 52C32545-A747-4A09-AE03-88ED20886AC1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 94F72505-68A6-47A0-A468-A8F54899212C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6E9ECFAE-9582-4E9E-85FA-F4905FB0211D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1DEB9093-F9C8-4141-945E-84EF0D9F59A6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 90830177-3ECD-41B1-984E-4DFCC248E386 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2596018C-9D3D-4B95-92F8-D20B64585817 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0533FBB1-2530-4F1E-852A-97F91E7BDD57 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E6901750-293D-4020-9763-E4BF13B86BE6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B9402E74-1D5F-4694-9AAE-22F6ED966BC0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ECDE4924-D07C-4BF1-9948-0DF9F77EAA06 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8BA3F57C-8CD0-4272-85AC-D974C395556E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 377E9136-C97F-48AF-9FBE-53B2E7F7DFE7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4FAB2363-B6BE-4E20-9EAE-2BB6C98137F9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 43593749-97D5-42D0-B02E-DB944049DEB0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 20A19674-084C-4F11-8933-06112A7F772C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EB41830E-1013-483E-B469-1A19A0F7D85E --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2026-03-04 '-XMP-ph:RideName=Colina da Matilde e Riacho dos Machados' -XMP-ph:RideDate=2026-03-04 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 82 — Colina da Matilde e Riacho dos Machados' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 82' '-XMP-dc:Subject+=PH 82' '-XMP-ph:RideCodes+=PH 82' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 85 — 25 foto(s) ===
DEST='/Users/danlessa/pedais/2025-03-25 - PH 85 - A Voçoroca e o Pântano'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid BC8D7AC2-F084-42FC-8855-0E34DCBEA5CC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E986B49C-230E-4233-A320-CE9B9CB4DD3C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F1825ADA-7897-4763-A1A1-FDA74EC76CF4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0969C2F3-F150-43E3-A4BD-C2AD15FF7B01 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 19CE3E76-62C1-45DE-9AFA-B9F84180713B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 89EE82F2-8FAF-4109-B546-B2F6C123E9B2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F079BCB9-8836-4849-9691-75F7BF6A2253 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F799B96D-7C3E-4E4F-900B-2B234AF2B52F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1B7FCBF7-9C9D-424F-9C51-1B4DF042E2E6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5B68E432-D018-44BC-8201-70FE38FB74FC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 65EF5E95-799F-499E-A2AF-A741D2466E98 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A991426A-1F41-4757-A7BB-04F09E1A3669 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F1283DEE-8F09-4CBB-8B59-362CC0084A3F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1E982BF9-12DB-40D3-945E-2BD78F9C4F19 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5231208B-707D-49D6-ABB2-F336161F7BB2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DD366527-A571-4E37-90B6-12458446D186 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0C68860E-7C60-4F65-9463-5E37BC2661FC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EAC42676-EDBC-4644-AAA7-18B470CFB7A6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 18804593-4141-4269-8D43-018AB3872A56 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F03581FC-B26A-4E23-9B09-607A4E8AEA81 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2883FA7F-68F1-432E-BEED-DF66E5BF449F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1A216254-B664-486E-AE05-784A9CAE67A3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6089EBDE-3227-40EA-B01C-31CA102B71F2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 35C64651-AA9D-478C-9F82-B81AFADDE75D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D29C4D62-3C8C-41BD-B053-B1DB2B35A01F --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-03-25 '-XMP-ph:RideName=A Voçoroca e o Pântano' -XMP-ph:RideDate=2025-03-25 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 85 — A Voçoroca e o Pântano' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 85' '-XMP-dc:Subject+=PH 85' '-XMP-ph:RideCodes+=PH 85' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 86 — 52 foto(s) ===
DEST='/Users/danlessa/pedais/2026-03-31 - PH 86 - Águas de Março- povo, éguas, lágrimas, alagados'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 1E7EF6B4-15ED-4EF1-BA81-E3B7BBCBFEA4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8FEFBA25-F23E-4820-86D1-CEB2CCE6FE2D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E392E32D-75B1-490F-91A1-9E3F9269B6D0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CEFBC5D9-C484-4D56-9CD7-9A4206AD8B6E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 27B1D9E8-F44B-412D-BD37-DA73E5ABC8C5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DC154BED-3EA9-4C5D-B4EA-165BDBD26763 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D806D21D-CB41-4A5C-8DFF-7DB6FFA5680B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8816FF9A-5DF4-4F27-A146-03818FAF28C2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 461D49BD-7A84-4B49-8732-69307AEB6BD1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3A4911B3-A8FA-4D95-941F-953D2273FB1B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CCC5D1C6-8EF5-4355-8810-57579B9C8C0B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4986D758-AEC6-4628-9FCF-9EB4B63778E9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 47CB2619-BFE4-4419-AF88-DD1FFADB1EEB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D00B7E6F-55F8-4577-8909-507D2E7D4BB7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E93C4709-81A7-4ED3-A90B-2573B4382A7F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F2AC822E-143D-49D7-8439-191AE1BAA72A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7AC72852-147C-4224-B5F7-93333FD496B6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A3C50D89-FD77-4364-8AF3-C3EEF490561B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7CEE5099-A55F-405B-A41D-18835AD0C430 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 157550D5-3FD6-4BC8-81C6-69D5231C2D8B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CB91908C-6A4A-40DB-B897-19293AB232D4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6D4465AC-7D18-4752-A1A8-E65793F4C1F7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6096A8A8-2C39-4150-828B-F8EE273B2F10 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CD81522A-CE5C-4F78-B569-2349C6336365 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7288EBAD-0C56-486E-858C-18A8E500089E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E54C91DF-4B8F-43EB-9D2A-B3CF37CAE482 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D70119D3-B4EC-4F02-AABE-0D214450EA18 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 25799093-C77F-457A-B262-B7349C6344EE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9DDB87AF-6E2D-4544-AA47-98AA74619A6A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 190EAD44-72EE-4ECC-A342-2D583015D81B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8714ACEB-AF06-4B62-8ADC-B1970BC3AEE4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CA7A7468-238A-47A5-801A-D7A3BF3BC950 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5B65D4C8-0124-4831-8659-686A17EC15D5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 10E890CE-10AD-4E9F-AB4F-68D80482D767 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BE3FA8E9-C58A-4423-B5C1-62432E6185D1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D2B87764-2D2E-469D-81CD-CFD413B3B0BA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A060B085-FC7F-4483-8CFE-B8E87B1FD9A0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A022C795-A281-428E-96A9-8844566DBD56 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EA793B55-0520-4BF4-A272-798044D24CFB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 40C76873-6029-443A-98FD-81A28A97EB5D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2AC1742E-8178-49D7-A32E-23D8AC1E905E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9D6E715C-1592-4D98-B928-C85587CFAC21 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 53442400-2B5D-4A47-9963-DFAAF7CC7AB0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E0EC099A-B977-42C5-B3C0-F6FD54F5677C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E6613C33-66D5-4EA0-B5B1-19064639F173 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2AD4A8A7-46FF-476A-8A36-FC332FC7925C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5ABD4701-3E1E-45AF-B981-DE95147DBAD8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C336053C-EF94-435C-86EF-A0E2111215DF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 62EC073C-02C5-497A-924D-D4AEF57BC487 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 735F4A5D-5883-4CEE-AC8B-C902E338C733 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8F2743C9-3432-48DB-982A-A125FF944823 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 580EAD14-D9B9-4F7A-9E15-5627ADC1ADE9 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2026-03-31 '-XMP-ph:RideName=Águas de Março: povo, éguas, lágrimas, alagados' -XMP-ph:RideDate=2026-03-31 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 86 — Águas de Março: povo, éguas, lágrimas, alagados' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 86' '-XMP-dc:Subject+=PH 86' '-XMP-ph:RideCodes+=PH 86' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 87 — 13 foto(s) ===
DEST='/Users/danlessa/pedais/2026-04-14 - PH 87 - Várzea do Tietê e as origens do Futebol'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 0AAF7510-FB04-4C20-88D0-CA833E3BF680 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FDA8EAC3-719F-4BC0-9E63-22A9ADA157AA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AF613473-3A19-4307-8E34-3F042741A551 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0FAFD869-5E3F-49A3-B1CF-D9CD58249546 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A528874D-3345-4912-9681-D50BC481724C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6CF88F3A-F6AE-4662-9E91-F06B62355ECB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9833C6D9-2535-4B3F-A801-4886A3853619 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 205A7ED4-94CB-4373-84E4-54516CD4C049 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 972B4C9F-6C4E-4A4A-B38D-C4C937AF792B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 39736A30-3F3D-4070-B148-036F6A586D08 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 96BEF314-95AA-4308-9F9D-F29F3EC9C324 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D55F93A1-1343-4389-B673-3E065C14BD36 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F51C33E6-4D9C-4D97-8A64-193B3079E6FA --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2026-04-14 '-XMP-ph:RideName=Várzea do Tietê e as origens do Futebol' -XMP-ph:RideDate=2026-04-14 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 87 — Várzea do Tietê e as origens do Futebol' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 87' '-XMP-dc:Subject+=PH 87' '-XMP-ph:RideCodes+=PH 87' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 89 — 41 foto(s) ===
DEST='/Users/danlessa/pedais/2026-04-28 - PH 89 - Pontos de Sela dos afluentes de Tamanduateí'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid F060B93D-F61B-4C8E-9B90-1D669B7E6DB2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 34293005-3C1A-4CBA-9C31-0F3FC7FC0DBD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CF3C6FDA-37A8-4E62-8097-CD9A123A26AF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E33C10DE-1117-4849-AEC7-A8A414794A72 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F040DD0C-6C80-4ED7-819E-65D6A3984495 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B5386E30-1165-4B26-9494-2D0AD9260669 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 57D01989-7204-42E7-9E75-0D717B09C8C6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1CCD24E2-C8B9-441A-A153-C46DC5172B7F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3B29B0B5-4E9F-49EF-947E-7E9E241F5BE2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6A5D20B3-E74F-4F16-8A4B-A734FF13536C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 67437834-D70A-4BBD-8A45-14D9F57A86F0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 058296D4-9E81-48AF-AE1C-01948E4FE836 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E9389F93-E165-4723-B47D-2F4CD06AA70F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 565FD96F-F202-478E-A751-B012C5659455 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1B182AF3-9EFB-4C4F-A9FF-CB5DAC9003FF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 89A87DFB-B7AC-48EE-88C0-9E0541CD0FF8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 45DAEE6D-9CFE-4304-B8C6-611E04F75248 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid ADB92E01-D525-41DB-9A0F-1A17F7615C21 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F691D3D7-1315-45AB-8685-24DADE2AE77F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 64433498-E511-4EAC-96B2-A9B5450491D1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 20AD4FEA-A306-45CA-B7C2-A119ADF58BE1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 388AF9DF-A42E-41AA-A664-C499F85906DE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8848EA4F-1D65-44C9-8CDF-071C50341FD8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A5E9AFF3-9A2B-4D16-B4B3-0A04A99A3149 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 132010C5-487A-408B-89B2-583C1C493FB7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 137FD293-D6C5-4192-ABBB-32EC46F5D5C0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 054318D8-2A61-42B6-9558-D6F51997848E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A32B9109-CFB4-42CD-885B-F298CFC78B48 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 65702626-F2B2-4C39-A831-E834F6BD34F4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 432EEF50-117F-494D-B05D-CE4D5B940AA2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5CB4B953-BD06-468F-83B9-690A9F8A2A1D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4F48C3F6-EC0E-4DBF-B7DD-573C5F9CEAE2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9E2D8CAA-8547-4A78-86C0-C7885A7148CF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A76EA8EC-491D-464F-9B47-3E9AE3BB5962 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5E24F411-1164-4DF4-8F70-42DC9E3F3E89 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7ED53D53-3175-45A0-9BDF-18B592F69E79 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A1755A02-5C75-4EC7-952E-8E7F6803243D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 48A01585-EE3F-42EF-AD28-D9BAD69AEBDC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 53757B0D-0C3D-4E7D-B623-875FF54DE007 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8E0AAF2D-4A17-4583-A3AF-F83EF8B205F6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8D94FB7D-A5D5-4E29-A164-710673119ABA --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2026-04-28 '-XMP-ph:RideName=Pontos de Sela dos afluentes de Tamanduateí' -XMP-ph:RideDate=2026-04-28 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 89 — Pontos de Sela dos afluentes de Tamanduateí' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 89' '-XMP-dc:Subject+=PH 89' '-XMP-ph:RideCodes+=PH 89' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 90 — 50 foto(s) ===
DEST='/Users/danlessa/pedais/2026-05-06 - PH 90 - Subir Gamelinha e Contornar Rincão pela Crista da Penha'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 469D0B71-1C48-425C-BFD1-29C61E5F1F6F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B10BEAB8-6252-4374-99E4-D981E65880F8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9F75F1B7-3378-4ADB-9C07-D0F2F5226CD4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D55507F1-1B6B-464F-8F1F-53224A76BA52 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A84C5729-6CE2-4ED9-AE81-8111A1687A31 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AAFCA3AB-4B18-426C-A864-5C451880293F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E209E713-B368-4D5E-8906-3BEC85B8F6CA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4A9140D2-1CCB-4BC7-A0B9-CF2A059BF9FD --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 70EDE82E-A04C-49C7-9998-B18744CEF06F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 00259E9A-3507-401E-8C92-B68034231001 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A32A6CB7-FFF3-48A2-9AEE-0B2B56256881 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5F2F352F-417A-42D5-A598-EB69E27FA837 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 72D7EC84-3A44-4955-A394-B725CE94C20F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E8A9EB99-4A6D-4ABF-B3D8-45439CBF8E28 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2A22DF9F-869E-42F0-A48D-7ED38920D3BF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6EBC80E4-CED0-41FB-BB63-2EB90E31A68A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FFAB90BA-2A6D-4F61-B497-36438AE1662B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B5F638D1-ED0B-4389-87E6-E9B942DE785D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0DE38FD7-397A-49D5-AA11-8EFA2A4A64D1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5EF9505C-C99C-4312-871A-D8389EC03F07 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 194A3776-FFF9-42E1-84E3-D9CD6FF21104 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BC52A35E-5B9F-4529-B29A-BF19A7875D01 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1FBBCE5D-E752-4589-91E0-7CFC1D38EAB1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 525ACE4D-0538-4D57-BECD-B062FDC8F653 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2F946144-1F8D-4808-B6F5-8C46C5AED228 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 345E9B71-7E14-437A-95DF-373231070B36 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 30FCD7C1-B17A-42CF-A8BB-92CA972B5360 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7B230792-0AE7-4B3B-B242-FD5E5D40CA2E --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1B5BB7C0-E74A-49E8-84D5-E688292B165F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EB82F71D-64DB-48DC-A748-586D681C9B3A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C5183C19-C029-421B-93DD-1F89AEFB25A8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 271C2B74-44A0-400C-9395-AAF4901FBEFF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7733E61A-9A16-4E48-AF94-4735EC7AAFC1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 19887F4D-5CD6-40D0-8F5E-C3AFC6DBF6C4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 27B28B88-803E-42E0-8EE6-944383AF238F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 25099F06-061C-40FD-A84C-767FD1907639 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5602BEE1-1027-45AB-8507-64B118A87651 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1AA43378-2585-4CE5-A95C-2D8067EE8D3A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2CAA30CB-D55E-4018-8E35-06DA4178C496 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8062A637-69E3-4641-93C9-E99442A3F063 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4CDC6C44-48D6-4366-8804-E624FE0D3099 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0756E521-7EEE-4E56-A5B9-8FA03E2AE475 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 363EFFB5-FDE7-41AB-9251-00B6CB017653 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B19C8452-B8B0-4AD4-AE39-4C3AD256E2E0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 71B987BD-42E1-4FF3-9465-6D841F5179A7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 79329C8F-BB4F-4867-AEE3-DF7712AA1103 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 26B02444-0F46-4C79-8692-E324BF0022BE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 83474417-8B52-48CD-B150-CE2CE6DF2EC1 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 5D4A12C8-01FE-42C4-AFBA-FE7B5E435960 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2E5BE3E9-AFF5-45BB-9B75-8027CD9668D3 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2026-05-06 '-XMP-ph:RideName=Subir Gamelinha e Contornar Rincão pela Crista da Penha' -XMP-ph:RideDate=2026-05-06 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 90 — Subir Gamelinha e Contornar Rincão pela Crista da Penha' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 90' '-XMP-dc:Subject+=PH 90' '-XMP-ph:RideCodes+=PH 90' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 92 — 2 foto(s) ===
DEST='/Users/danlessa/pedais/2025-05-13 - PH 92 - Crista do Lauzane, subir Água Fria e duas vilas escondidas'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 889C3641-7887-4C5A-BA74-EC6E45005C45 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 236F0565-D9CD-46C7-8F46-D74983DC300F --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-05-13 '-XMP-ph:RideName=Crista do Lauzane, subir Água Fria e duas vilas escondidas' -XMP-ph:RideDate=2025-05-13 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 92 — Crista do Lauzane, subir Água Fria e duas vilas escondidas' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 92' '-XMP-dc:Subject+=PH 92' '-XMP-ph:RideCodes+=PH 92' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

# === PH 93 — 79 foto(s) ===
DEST='/Users/danlessa/pedais/2025-05-20 - PH 93 - Ziguezaguear a Crista do Morumbi'
mkdir -p "$DEST"
osxphotos export "$DEST" --uuid 083383FA-8317-4A76-893E-E1279397B2AE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8239453F-FB24-4BE0-AA8D-D26646F09237 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 720A97C2-13AE-4E08-AF33-B47158DC1F90 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DC9CCA7B-85E5-4504-8618-21B552E0DD24 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0BE61AF5-EC87-42E5-9DDD-5454C3F02672 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6156D70B-2142-433B-BA1F-B8B33C099D71 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 88038F4D-5919-47A6-B2D5-E75F41D06334 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FB3C9863-6CB7-46DD-A41E-69BBB9A4FEF9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 26607D87-0BF9-455F-972F-D877DF3DCAC0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FA386A71-26BF-4795-BC8F-DABC8CAB36A9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7456E28C-DA20-4823-8D98-52C437D9A73C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 85D22CBE-FED7-4429-BA11-230C6E53B8BC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8DBDB2E0-829F-4C1B-ADF6-DD30C21783BA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 64C7D64A-1673-41D3-B99A-6D7C59787BD0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 9F80C121-B337-4826-B958-967ABB0D5896 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6DA86411-AFCF-418F-8AF3-60FBA7FB6939 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 15680519-CF2C-46EA-9473-3AA4CFDDBB8A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid DE4E32E0-E15E-4373-9FAA-3FA6752ADEA4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A88A5CC2-9ECB-437C-8593-8D27FBFBF157 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1FCAE1D9-A2E1-4254-8E11-1F71A50CF955 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C5D9B30D-6EDE-4F59-9AA9-4BC7CB205683 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FBAA2049-35D4-4427-9A67-D5F2565F962B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid B7B77E8C-F1AA-4483-B746-11E1ADAEA6FF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid E7AFAF8D-98D0-4B49-8A78-ECF1CC91F76B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 300C34F7-E84F-4503-B618-604969A497A6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7E975FEC-ABE3-4CDC-A8A8-A68646F35D5B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BA31CB4D-C03E-4D42-914F-BCBE8062DE56 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 73ACE262-9BA3-4C18-8C36-AE57B3906EA0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid CCA46378-0DDD-4F32-B365-6490A238E882 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 74A6F0AF-4201-4EC0-85EC-79041D02F721 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 7A10F613-5E86-4FF5-89C8-7592B6AC575B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid AD9F9115-BF49-4560-8518-C464659CF450 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 36E5CF68-4162-4C45-968D-3D485D212FC6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid EBC0B24B-D575-4040-8419-C69807A94E61 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 1DA0E0C8-3763-49A9-A33C-D01A82FBB79F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 49475890-4398-4112-ADF6-D0B69BBE344F --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3D14D4B4-4DF2-4860-8D8F-FA59CC3837B7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 0586E4F0-67F6-4AB0-8F97-D9D2821095D8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FC775C1B-5F09-4DA5-B26C-7CDBACE87221 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6EE17238-AE26-4841-8777-476FEAA63CF9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D6885481-4443-454B-AA2E-2E7A305710D0 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid C0C269A4-4EEF-4B48-9D5F-F49BBF763D8B --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6B2B2BE2-A932-42D4-BD10-E889700FAA1D --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F0005965-388E-4FC2-8C40-8B3C43E6C4F7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 362CC00F-0744-4229-B48B-49D8E3AA1B78 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8F94F091-9C84-4521-BFE1-6F35A87C02FA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A4654410-F588-49B0-A30E-A73D5809C730 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2B55BE81-6ED8-41F0-B8A8-DAD864386DEB --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 39C43AD5-F50E-4A67-9A0A-1F39CE948112 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BE99112B-3520-4B9D-966C-EC75DD6971AC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A50BE9CA-921B-40CF-BB43-3009AEC407A4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 709B8B16-32FA-4364-A7C6-36FA19D191F2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A4C6E831-32A5-4EDD-A789-8256EE2750D8 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid A600D85A-5CFB-4504-8CA8-C7CF0116F745 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3DADFAFB-3A50-4F98-A98A-23298D31CBAA --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 2C508401-6C6C-48A1-ACB3-0D58C9D18971 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6133AF0F-86BE-4CF4-8A6C-9E03F24A5BC4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 392813B7-E814-4C1F-A2D0-23CD41DAF903 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid F4C9BD74-C9C9-4C3B-B7D0-87C3AF5DE9D5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BCE0DD7D-A5C0-40FA-81C5-46F00D8DFF18 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D1C453EA-FA12-482A-9CD9-9E5F10526CCE --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 3561707D-670B-40BD-A142-1C89DF7E2083 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8DA24972-0E28-477C-9F1A-934B1F186D99 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4E0B0D14-EE47-4246-952B-44562291D4D3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 821628A5-61A2-4DC3-BA57-CB8D4745B6C2 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 8C97FD70-2ABD-4C1B-A58A-71E9EB01F2E7 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 96E98294-72DC-49C0-8356-5F8B8A128A77 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 4A51978D-CBA7-4C81-BB40-6F0D1470C1B6 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D302646D-EA69-4E59-A05E-31A3611353F5 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 63D857A7-B5CA-4423-ADB5-FD31EF1EEFCC --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 77A48B94-0C38-4876-93C4-02F7562776E9 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid FB92EA08-0D1A-42DE-BAB1-7BABBFA9D41A --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 696C443C-7847-4817-A1B7-BBA72957041C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 75BEAC6C-9E81-4A63-B56A-5CA490C08EF4 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 551EC783-ED29-4AD1-89B4-3A854416785C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid D425F363-1FED-4AC6-A845-F40CBC90354C --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid BD143A66-0F36-40DF-BAF1-6089C32FF3AF --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 20DC49D1-1531-44BD-9A64-C1B8F9656BC3 --skip-edited --download-missing --retry 3 --update --ignore-signature
osxphotos export "$DEST" --uuid 6FBC7FB3-8E64-4BAE-BD44-B98FD7307B12 --skip-edited --download-missing --retry 3 --update --ignore-signature
exiftool -config /Users/danlessa/repos/pedalhidro/pedalhidrografico/scripts/exiftool_ph.config -overwrite_original -q -api NoDups=1 -XMP-ph:CapturedDuring=https://pedalhidrografi.co/id/tour/2025-05-20 '-XMP-ph:RideName=Ziguezaguear a Crista do Morumbi' -XMP-ph:RideDate=2025-05-20 '-XMP-ph:Collective=Pedal Hidrográfico' '-XMP-dc:Description=PH 93 — Ziguezaguear a Crista do Morumbi' '-XMP-dc:Subject+=Pedal Hidrográfico' '-XMP-ph:RideCode=PH 93' '-XMP-dc:Subject+=PH 93' '-XMP-ph:RideCodes+=PH 93' -ext jpg -ext jpeg -ext heic -ext heif -ext png -ext tiff -ext tif -ext dng -ext raw -ext cr2 -ext cr3 -ext nef -ext arw -ext mov -ext mp4 -ext m4v -ext gif "$DEST"

