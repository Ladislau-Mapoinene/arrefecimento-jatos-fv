# Arrefecimento de módulos fotovoltaicos por múltiplos jatos de impacto

Dados experimentais e código de tratamento da dissertação de Mestrado em Engenharia Mecânica
**«Análise da Transferência de Calor por Múltiplos Jatos de Impacto para Arrefecimento de Módulos
Fotovoltaicos»**, Universidade do Minho, 2026.

O repositório permite reproduzir, a partir dos dados brutos, todas as tabelas e figuras de resultados
da dissertação: ensaios laboratoriais (módulo de 545 Wp aquecido com 349 W, sem e com placa perfurada,
a 30, 40 e 50 Hz), monitorização exterior (Arduino e Victron, junho e julho de 2026), simulação anual
com dados horários do PVGIS e avaliação económica.

## Estrutura

```
codigo/                 scripts numerados (ver tabela abaixo) e config.py
dados/brutos/           ficheiros originais, não alterados
  Analise_geral_16.10.xlsx    ensaios laboratoriais de 2 e 9 de outubro de 2026
  repeticao_16out/            repetição do ensaio CP30 (16 de outubro de 2026)
  termografia/                imagens termográficas (SP e CP)
  DATA10.CSV, DATA25.CSV      registos do Arduino na monitorização exterior
  Ensaio10_Victron.xlsx       registos do controlador Victron
  clima/                      séries horárias PVGIS 5.3 (SARAH3, 2019–2023), Beja e Guimarães
resultados/tabelas/     tabelas gravadas pelos scripts
resultados/figuras/     figuras gravadas pelos scripts
```

## Scripts

| Script | Função | Secções da dissertação |
| --- | --- | --- |
| `config.py` | Constantes medidas e derivadas, propriedades do ar, geometria, formato das figuras | Todas |
| `01_lab_reanalise.py` | Calibração in situ, arranque do ventilador, valores finais, UA | 3.5.1, 4.2.1 |
| `02_lab_comparacoes_figuras.py` | Comparação a caudal e a potência de bombagem iguais; ζ da placa | 4.2.3, 4.2.4 |
| `02b` a `02f` | Evolução temporal, termografia, repetição, mapas 3×3, velocidades | 4.2, Anexo 4 |
| `03_exterior_sincronizacao_modelo.py` | Sincronização Arduino–Victron, seleção e regressão | 3.5.2, 4.1 |
| `03b`, `03c`, `03d` | Figuras da monitorização exterior | 4.1 |
| `05_correlacao_economia.py` | Correlação de Martin, coeficiente efetivo, escoamento cruzado | 4.2.5 |
| `07_energia_conceito.py` | Simulação horária anual, protótipo e conceito, VAL, TIR, LCOE | 3.5.3, 4.3, 4.4, Anexo 7 |
| `08`, `08b` | Síntese quantitativa das técnicas de arrefecimento | 2.3 |
| `09_incertezas.py` | Balanço de incertezas | Anexo 6 |

## Execução

Python 3.11 ou mais recente:

```
pip install -r requirements.txt
cd codigo
python 01_lab_reanalise.py
python 02_lab_comparacoes_figuras.py
...
```

O `01` deve ser executado antes dos restantes scripts laboratoriais, e o `03` antes do `03b`, `03c` e
`03d`. O `07` usa os resultados do `01` e os dados do PVGIS. Em Jupyter, a partir da pasta `codigo`:
`%run 01_lab_reanalise.py`.

O `02c_termografia.py` requer o programa gratuito [ExifTool](https://exiftool.org) para extrair a
temperatura das imagens. As figuras usam o tipo de letra NewsGotT, se estiver instalado; caso
contrário, usam o DejaVu Sans.

## Licença

Código: licença MIT (ficheiro `LICENSE`). Dados: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

## Citação

L. Mapoinene, «Análise da Transferência de Calor por Múltiplos Jatos de Impacto para Arrefecimento de
Módulos Fotovoltaicos», Dissertação de Mestrado, Universidade do Minho, 2026.
