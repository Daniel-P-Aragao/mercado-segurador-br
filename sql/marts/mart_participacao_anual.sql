-- Grão: ano x segmento x seguradora
-- Participação de mercado por prêmio direto; índices técnicos sobre prêmio ganho.
CREATE OR REPLACE VIEW `{projeto}.susep_marts.mart_participacao_anual` AS
WITH base AS (
  SELECT
    EXTRACT(YEAR FROM f.data) AS ano,
    COUNT(DISTINCT f.data) AS meses,
    r.segmento,
    f.coenti,
    SUM(f.premio_direto) AS premio_direto,
    SUM(f.premio_ganho) AS premio_ganho,
    SUM(f.sinistro_ocorrido) AS sinistro_ocorrido,
    SUM(f.desp_com) AS desp_com
  FROM `{projeto}.susep.fato_seguros` AS f
  JOIN `{projeto}.susep.dim_ramos` AS r USING (coramo)
  GROUP BY ano, segmento, coenti
)
SELECT
  b.ano,
  b.meses,
  b.segmento,
  b.coenti,
  c.noenti,
  b.premio_direto,
  b.premio_ganho,
  b.sinistro_ocorrido,
  b.desp_com,
  SAFE_DIVIDE(b.premio_direto, SUM(b.premio_direto) OVER (PARTITION BY b.ano, b.segmento)) AS participacao,
  RANK() OVER (PARTITION BY b.ano, b.segmento ORDER BY b.premio_direto DESC) AS ranking,
  -- Índices só quando o prêmio ganho anual é de pelo menos R$ 10 milhões
  IF(b.premio_ganho >= 10000000, SAFE_DIVIDE(b.sinistro_ocorrido, b.premio_ganho), NULL) AS sinistralidade,
  IF(b.premio_ganho >= 10000000, SAFE_DIVIDE(b.desp_com, b.premio_ganho), NULL) AS comissionamento
FROM base AS b
JOIN `{projeto}.susep.dim_seguradoras` AS c USING (coenti)
WHERE b.premio_direto > 0;