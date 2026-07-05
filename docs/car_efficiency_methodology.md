# Metodologia — comparação energética bike × SUV

Este documento descreve como o **amora** estima, ao editar um traçado, quanta
energia um **SUV a gasolina** gastaria na mesma rota e quantas vezes a bicicleta
é mais eficiente — incluindo a escolha dos parâmetros físicos e sua calibração
para a realidade de São Paulo.

O código vive em `web/app.js`: `carEnergyJ()` (integração por segmento),
`powerForCar()` / `speedForCar()` (perfil de potência do SUV) e a seção de
exibição em `updateMetrics()`. Os parâmetros ficam em `DEFAULT_PARAMS` (chaves
`car*`) e são **editáveis** pelo usuário no modal *Parâmetros → Comparação com
carro (SUV) → Parâmetros do SUV…*. Este doc registra os **defaults** e o porquê
deles; qualquer usuário pode ajustá-los.

## 1. O modelo

O SUV usa o **mesmo modelo de energia v2** da bicicleta
(`bicycling-energy-model/notas.md`), integrado **segmento a segmento** sobre o
mesmo perfil de elevação (com *deadband*) que a rota da bike usa:

```
E_seg = α_r·x + α_a·x  +  β·Δh⁺  −  ε·β·Δh⁻
α_r = m·g·C_rr / η          (rolamento, por metro horizontal — sempre)
α_a = ½·ρ·C_dA·v² / η        (arrasto, por metro horizontal — SEMPRE, ver §2)
β   = m·g / η                (gravidade, por metro vertical)
```

onde `η` (no código `carKEff`) é a **eficiência de conversão químico→roda**
(tanque-para-roda): a fração da energia química do combustível que vira trabalho
de tração na roda. Dividir os termos mecânicos por `η` os converte de energia
mecânica para **energia de combustível**.

A velocidade `v` de cada segmento vem do equilíbrio de forças, resolvido pela
mesma cúbica da bike (`solveSpeedAtGradient`), mas com o **perfil de potência de
3 níveis do carro** (`powerForCar`): potência de subida / plano / descida,
escolhida pelo gradiente do segmento em relação ao `carSlopeFlatThreshold`.

### Diferenças físicas em relação à bike

1. **Arrasto cobrado em 100 % da distância (f = 1)**, inclusive subindo. A bike
   desacelera o bastante numa subida para zerar a contribuição aerodinâmica; o
   SUV mantém a velocidade do seu perfil de potência o tempo todo, então o
   arrasto nunca some.
2. **ε (recuperação na descida) é um valor FIXO** (`carEpsilon`), não estimado
   do perfil da rota como o da bike. Ver §4 — é o parâmetro mais delicado.
3. **v_f próprio do SUV**: a velocidade de cruzeiro do carro vem da sua própria
   potência de plano, não é herdada da bike.

## 2. Energia de "entrada" dos dois lados

A razão de eficiência compara **energia de entrada** (o que foi *consumido da
fonte*), não trabalho mecânico:

- **SUV**: já é energia de combustível (mecânica ÷ `carKEff`).
- **Bike**: a energia "nas pernas" (`eLegJ`) é só a saída mecânica do ciclista.
  O corpo humano converte ~25 % da comida em trabalho, então a energia
  **metabólica** (comida consumida) é ≈ 4× isso (`bikeMetabolicFactor`).

```
razão = energia_combustível_SUV / (energia_pernas_bike × fator_metabólico)
```

E a estimativa de **litros de gasolina** = `energia_combustível_SUV / 32 000 kJ/L`
(`GASOLINE_KJ_PER_LITER`).

## 3. Calibração para São Paulo — 10 ± 2 km/L no plano

**Meta:** o SUV deve fazer **10 ± 2 km com 1 L de gasolina no plano**.

No plano, `Δh = 0` em todo segmento, então a economia depende **só** de `carKEff`
e da velocidade de cruzeiro `v_f` (via `carPowerFlat`):

```
combustível_por_metro_plano = (m·g·C_rr + ½·ρ·C_dA·v_f²) / carKEff   [J/m]
km/L = 32 000 000 / combustível_por_metro / 1000
```

Com os defaults abaixo: `v_f ≈ 64,8 km/h`, `combustível ≈ 2 977 J/m` →
**≈ 10,75 km/L** (dentro da meta, centralizado). Massa, C_rr e C_dA não entram na
calibração da meta — foram fixados pelo usuário — então a meta é atingida
ajustando **`carKEff` e `carPowerFlat`**.

### Parâmetros e sua fundamentação

| Parâmetro | Default | Fundamentação (literatura / SP) |
|---|---|---|
| `carMass` | 5000 kg | Fixado pelo usuário (pesado p/ um SUV de passeio ~1800 kg; mantido). |
| `carCrr` | 0,013 | Rolamento no asfalto: literatura 0,010–0,015; pneus de SUV no topo da faixa. |
| `carCdA` | 1,1 m² | C_d ~0,38 × área frontal ~2,9 m² — extremo "SUV grande/boxy" (central ~1,0). |
| `carKEff` | **0,28** | Eficiência tanque→roda em **cruzeiro estável**: fueleconomy.gov "energy to wheels" 22–30 % na estrada; BTE de motores SI modernos ~30–36 % × ~0,9 de transmissão. Faixa defensável 0,25–0,30; central 0,28. (Ciclo combinado ~0,21–0,25 = o "cerca de um quarto"; média de ciclo com cidade ~0,16–0,20.) |
| `carPowerFlat` | **15 000 W** | Cruzeiro de equilíbrio ~65 km/h — arterial de fluxo livre em SP (entre os 50 km/h de arterial e os 80–90 km/h das Marginais). |
| `carPowerAscent` | 45 000 W | Motorista **acelera na subida** — em SP não se "cruza" em morro (acelera e freia). ~69 / 50 / 35 km/h a +3 / +5 / +8 %; sobe grades leves acima da velocidade de plano. |
| `carPowerDescent` | 0 W | Pé fora do acelerador (corte de combustível na desaceleração — DFCO). |
| `carSlopeFlatThreshold` | 0,03 (±3 %) | Grade de equilíbrio do *coasting*: acima dela, na descida, o motor tira o pé e entra o DFCO. Literatura: ~1,5 % (cidade) a ~3 % (estrada) — usamos o extremo de estrada. |
| `carEpsilon` | **0,20** | Ver §4. |

Referência de economia real (INMETRO PBE Veicular / testes): SUVs a gasolina no
Brasil fazem ~10–12 km/L cidade e ~12–14 km/L estrada (Compass, Taos, Tiguan,
Corolla Cross, Tracker). ~10–11 km/L é uma cifra de cruzeiro plano conservadora e
coerente — lembrando que o veículo modelado aqui (5000 kg) é bem mais pesado que
um SUV real, então tirar 10 km/L dele já exige uma eficiência generosa.

### 3.1 As potências são plausíveis para 5000 kg?

**Importante:** `carPower*` são **potências mecânicas de tração (na roda) em
equilíbrio** — NÃO a potência de pico do motor. A cúbica
`solveSpeedAtGradient` resolve `potência = F_resist · v`, então a potência é o
que a roda entrega para manter a velocidade naquele terreno. A potência de
combustível equivalente é `potência_roda / carKEff`.

| Regime | Roda | Combustível-equiv (÷0,28) | Velocidade |
|---|---|---|---|
| Cruzeiro no plano | 15 kW (20 hp) | ~54 kW (72 hp) | ~65 km/h |
| Subida (pico do modelo) | 45 kW (60 hp) | ~161 kW (216 hp) | 69 km/h @+3%, 50 @+5%, 35 @+8% |

No cruzeiro, os 15 kW na roda se decompõem em **~11,5 kW de rolamento + ~3,5 kW
de arrasto** — o rolamento domina justamente por causa dos 5000 kg. Isso foi
confirmado como fisicamente correto (inclusive escalando o *road-load* de um
caminhão Classe 8). A potência **máxima que o modelo já exige** é
`carPowerAscent` = 45 kW na roda ≈ **161 kW de motor** — bem dentro do envelope
de um veículo real de ~5000 kg (SUV blindado / picape pesada têm pico de
**~220–450 kW**, central ~300 kW), com folga confortável.

A potência de subida (45 kW) modela o jeito **paulistano** de encarar morro:
o motorista **acelera na subida** (acelera e freia, não "cruza") — o SUV sobe
grades leves (+3 %) *acima* da velocidade de plano (~69 vs. ~65 km/h) e só cai
de verdade nos grades íngremes (~50 a +5 %, ~35 a +8 %). É uma escolha
mediana-agressiva entre o cruzeiro suave (30 kW) e afundar o pé nos ~300 kW do
motor; editável no modal.

**Ressalva:** 5000 kg é território de picape pesada / SUV blindado / caminhão
leve — um SUV de passeio real pesa ~2500 kg. É a massa fixada pelo usuário; a
calibração compensa via `carKEff`.

## 4. O parâmetro ε (recuperação na descida) — e por que 0,20

`ε` credita de volta uma fração da energia gravitacional liberada **durante** uma
descida (`−ε·β·Δh⁻`). É o parâmetro mais sujeito a mal-entendido, então vale
detalhar o que ele **é** e o que ele **não é**:

- **É**: a energia potencial que, na descida, a gravidade usa para *propelir* o
  carro no lugar do motor. Acima do grade de equilíbrio (~3 %), um motor moderno
  corta o combustível (DFCO) e a gravidade faz o trabalho de tração que o
  combustível faria no plano → combustível evitado **naquele segmento**.
- **NÃO é** transporte de energia de um morro para o outro. O modelo **nunca**
  assume que o carro embala numa descida e "sobe de graça" o morro seguinte com
  a energia acumulada. Toda a energia **excedente** (cinética + o excesso de
  energia potencial além de rolamento+arrasto) que é **dissipada no freio** ao
  parar **já não é creditada**: `ε` é limitado a 1, e a ida-e-volta por um morro
  continua sendo uma **perda líquida** de combustível.

### Por que baixamos de 0,70 (idealizado) para 0,20 (São Paulo)

Uma primeira estimativa de literatura para descidas de fluxo livre com DFCO
sustentado dá `ε ≈ 0,7–0,85`. **Mas isso pressupõe descidas longas e limpas**,
que quase não existem no dia a dia de São Paulo:

- **O carro para o tempo todo** (semáforos, congestionamento — SP tem uma das
  piores médias do mundo, ~25–30 km/h na cidade). Cada parada joga fora no freio
  a energia cinética acumulada — que o modelo, corretamente, já não credita, mas
  que na prática também significa que o regime "coasting limpo" raramente se
  sustenta.
- **Grades rasos** (< 3 %) dominam a malha urbana. Abaixo do grade de equilíbrio,
  a gravidade **não** basta para manter a velocidade, então o **motor continua
  queimando** combustível — sem o corte que justificaria um ε alto.
- Há ainda um **piso de marcha lenta** (idle) que consome combustível mesmo com
  o pé fora.

Ou seja: o regime que sustenta ε ≈ 0,7 é o de estrada aberta e serra, não o de
São Paulo. A própria literatura coloca o trânsito parado/rasos em `ε ≈ 0,5–0,65`,
mas numa cidade tão congestionada — onde o carro para o tempo todo e joga no
freio a energia que ganharia na descida — mesmo isso soa otimista. Por isso o
default é **`ε = 0,20`** — recuperação **bem modesta**, assumindo que quase toda
a energia de descida em São Paulo se perde em freada e marcha lenta.

**Importante:** `ε` **não afeta a economia no plano** (a meta de 10 ± 2 km/L),
que independe de descidas. Baixar ε só encarece rotas com relevo — o que está
alinhado com a realidade de um carro que para o tempo todo. Uma rota ondulada de
±5 % de exemplo cai de ~10,75 km/L (plano) para ~6,9 km/L com ε = 0,20 (seria
~7,6 com ε = 0,40). Quem quiser modelar estrada aberta/serra pode subir ε no
modal.

## 5. Limitações assumidas

- **Modelo de equilíbrio, sem paradas explícitas.** Nem o carro nem a bike pagam
  pela energia cinética perdida ao parar e re-acelerar em cada semáforo — os dois
  são comparados em "cruzeiro". Isso subestima o consumo *absoluto* dos dois em
  trânsito urbano, mas afeta pouco a *razão* (ambos sofrem paradas).
- **Mesma velocidade não é simulada** — o carro anda no seu perfil de potência,
  a bike no dela; a comparação é de **energia na mesma rota**, não de tempo.
- **Massa de 5000 kg** é a escolha do usuário e é pesada para um SUV de passeio;
  a calibração compensa via `carKEff` para atingir a economia-alvo.
- Todos os parâmetros do SUV são **editáveis** no modal — os defaults acima são
  um ponto de partida defensável, não uma verdade fixa.

## 6. Fontes

- US DOE fueleconomy.gov — *Where the Energy Goes* (repartição tanque→roda,
  cidade vs. estrada).
- INMETRO — Programa Brasileiro de Etiquetagem Veicular (PBE Veicular), tabelas
  de eficiência energética de automóveis.
- Testes de consumo (Mobiauto e afins) de SUVs a gasolina no Brasil.
- CET-SP / Prefeitura de SP — limites e velocidades de fluxo livre (arteriais,
  Marginais, Rodoanel); TomTom Traffic Index (congestionamento de SP).
- x-engineer.org e referências de dinâmica veicular — C_rr no asfalto, C_d e
  área frontal típicos de SUV.
- Literatura de *deceleration fuel cut-off* (DFCO) e economia em descida de
  veículos leves.
- `bicycling-energy-model/notas.md` — o modelo v2 de energia (forma fechada
  α_r·x + α_a·x·f + β·(h⁺ − ε·h⁻)) reaproveitado aqui.
