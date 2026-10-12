-- Grão: ano x segmento (inclui o "Mercado total")
-- HHI = soma dos quadrados das participações em pontos percentuais (0 a 10.000)
-- CR4 = participação somada das 4 maiores seguradoras
CREATE OR REPLACE VIEW `{projeto}.susep_marts.mart_concentracao` AS
WITH por_segmento AS (
  SELECT ano, segmento, coenti, premio_direto
  FROM `{projeto}.susep_marts.mart_participacao_anual`
),
total AS (
  SELECT ano, 'Mercado total' AS segmento, coenti, SUM(premio_direto) AS premio_direto
  FROM por_segmento
  GROUP BY ano, coenti
),
unido AS (
  SELECT * FROM por_segmento
  UNION ALL
  SELECT * FROM total
),
cotas AS (
  SELECT
    ano,
    segmento,
    premio_direto / SUM(premio_direto) OVER (PARTITION BY ano, segmento) AS cota,
    ROW_NUMBER() OVER (PARTITION BY ano, segmento ORDER BY premio_direto DESC) AS posicao
  FROM unido
)
SELECT
  ano,
  segmento,
  COUNT(*) AS n_seguradoras,
  ROUND(SUM(POW(cota * 100, 2))) AS hhi,
  SUM(IF(posicao <= 4, cota, 0)) AS cr4
FROM cotas
GROUP BY ano, segmento;