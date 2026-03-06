--
-- PostgreSQL database dump
--

\restrict xbfJgmuHdD0uGXbyDHGty3S5T7CDd3PcJHmCfbMIJAUUCyGjKGfs2hpVUIqyrMH

-- Dumped from database version 16.11 (Ubuntu 16.11-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.11 (Ubuntu 16.11-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: indicator_texts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.indicator_texts (
    id integer NOT NULL,
    indicator_id text NOT NULL,
    language character(2) NOT NULL,
    name text,
    definition text,
    formula text,
    owner text,
    dimension text,
    sector text,
    is_auto_translated integer DEFAULT 0,
    translation_status character varying(20) DEFAULT 'official'::character varying,
    source_language character(2),
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.indicator_texts OWNER TO postgres;

--
-- Name: indicator_texts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.indicator_texts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.indicator_texts_id_seq OWNER TO postgres;

--
-- Name: indicator_texts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.indicator_texts_id_seq OWNED BY public.indicator_texts.id;


--
-- Name: indicator_texts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.indicator_texts ALTER COLUMN id SET DEFAULT nextval('public.indicator_texts_id_seq'::regclass);


--
-- Data for Name: indicator_texts; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.indicator_texts (id, indicator_id, language, name, definition, formula, owner, dimension, sector, is_auto_translated, translation_status, source_language, created_at, updated_at) VALUES (1, '1.6.1', 'en', 'Total investment (growth rates)', 'Represents the variation of total investment in both physical assets (machinery, buildings, and equipment) and intellectual property products (e.g., software, R&D, patents) within the mining sector. This comprehensive measure reflects the sector''s ability to enhance productive capacity, foster innovation, and drive long-term economic growth.', NULL, 'Indicator team', 'Investment', 'Manufacturing', 0, 'official', 'en', '2026-01-19 11:34:10.326441', '2026-01-19 11:34:10.326441');
INSERT INTO public.indicator_texts (id, indicator_id, language, name, definition, formula, owner, dimension, sector, is_auto_translated, translation_status, source_language, created_at, updated_at) VALUES (2, '1.1.3', 'en', 'MVA (Manufacturing Value Added), constant 2015 USD', 'In consistent with ISIC, MVA measures the net output of manufacturing after adding up all outputs and subtracting intermediate inputs. It is calculated without making deductions for depreciation of fabricated assets or depletion and degradation of natural resources. MVA is a well-recognized and widely used indicator by researchers and policy makers to assess the level of industrialization of a country. This indicator provides a good overview of a countryâs manufacturing size. With the information of manufacturing outputs and intermediate inputs, the overall productivity can also be obtained.', NULL, 'Indicator team', 'Output', 'Manufacturing', 0, 'official', 'en', '2026-01-19 11:34:10.326441', '2026-01-19 11:34:10.326441');
INSERT INTO public.indicator_texts (id, indicator_id, language, name, definition, formula, owner, dimension, sector, is_auto_translated, translation_status, source_language, created_at, updated_at) VALUES (3, '1.2.1', 'en', 'MVA annual growth rate', 'This indicator enables trend analysis of manufacturing productivity over time. Fluctuations are therefore able to be identified', NULL, 'Indicator team', 'Output', 'Manufacturing', 0, 'official', 'en', '2026-01-19 11:34:10.326441', '2026-01-19 11:34:10.326441');
INSERT INTO public.indicator_texts (id, indicator_id, language, name, definition, formula, owner, dimension, sector, is_auto_translated, translation_status, source_language, created_at, updated_at) VALUES (4, '1.7.1', 'en', 'Manufactured Exports per Employee', 'This indicator reflects the ability to produce and export of manufacturing. Instead of using the gross population as denominator, the denominator adopted for this indicator is the total number of employees in manufacturing, which is able to readjust the possible difference in the size of manufacturing workforce (as it may be disproportional with total population). This indicator is more effective when conducting international comparisons.', NULL, 'Indicator team', 'Exports', 'Manufacturing', 0, 'official', 'en', '2026-01-19 11:34:10.326441', '2026-01-19 11:34:10.326441');
INSERT INTO public.indicator_texts (id, indicator_id, language, name, definition, formula, owner, dimension, sector, is_auto_translated, translation_status, source_language, created_at, updated_at) VALUES (5, '2.5.2', 'en', 'Wage growth rate in mining sector', 'Indicates changes in income levels over time, reflecting economic conditions.', NULL, 'GASTAT', 'Wages', 'Mining', 0, 'official', 'en', '2026-01-19 11:34:10.326441', '2026-01-19 11:34:10.326441');
INSERT INTO public.indicator_texts (id, indicator_id, language, name, definition, formula, owner, dimension, sector, is_auto_translated, translation_status, source_language, created_at, updated_at) VALUES (6, '2.2.2', 'en', 'Gross mining value added', 'It measures the contribution of the mining sector to a countryâs Gross Domestic Product (GDP). It reflects the economic value generated by mining activities, including the extraction of minerals, oil, and gas, before subtracting intermediate consumption. This indicator is vital for understanding the role of mining in the overall economy, especially in resource-rich countries. A high gross value added indicates a significant contribution of the mining sector to national income, employment, and investment. It also provides insights into productivity trends and helps track the performance of the sector over time. Policymakers use this metric to assess the economic importance of mining, guide resource management strategies, and plan for sustainable development. It can also signal the potential need for diversification in economies where mining dominates, in order to buffer against commodity price volatility and ensure long-term economic stability.', NULL, 'Indicator team', 'Output', 'Mining', 0, 'official', 'en', '2026-01-19 11:34:10.326441', '2026-01-19 11:34:10.326441');
INSERT INTO public.indicator_texts (id, indicator_id, language, name, definition, formula, owner, dimension, sector, is_auto_translated, translation_status, source_language, created_at, updated_at) VALUES (7, '1.4.2', 'en', 'Female manufacturing employment', 'Measures the participation of  women in the manufacturing sector. This helps in understanding gender diversity, workforce inclusion, and the role of women in the industrial labor market.', NULL, 'Indicator team', 'Employment', 'Manufacturing', 0, 'official', 'en', '2026-01-19 11:34:10.326441', '2026-01-19 11:34:10.326441');
INSERT INTO public.indicator_texts (id, indicator_id, language, name, definition, formula, owner, dimension, sector, is_auto_translated, translation_status, source_language, created_at, updated_at) VALUES (8, '1.5.2', 'en', 'Labor productivity (Output per worker)', 'Labour productivity represents the total volume of output (measured in terms of Gross Domestic Product, GDP) produced per unit of labour (measured in terms of the number of employed persons) during a given time reference period. ', NULL, 'Indicator team', 'Employment', 'Manufacturing', 0, 'official', 'en', '2026-01-19 11:34:10.326441', '2026-01-19 11:34:10.326441');
INSERT INTO public.indicator_texts (id, indicator_id, language, name, definition, formula, owner, dimension, sector, is_auto_translated, translation_status, source_language, created_at, updated_at) VALUES (9, '2.4.1', 'en', 'Number of employees in mining sector', 'Tracks employment levels, providing insights into labor needs and workforce stability.', NULL, 'Indicator team', 'Employment', 'Mining', 0, 'official', 'en', '2026-01-19 11:34:10.326441', '2026-01-19 11:34:10.326441');
INSERT INTO public.indicator_texts (id, indicator_id, language, name, definition, formula, owner, dimension, sector, is_auto_translated, translation_status, source_language, created_at, updated_at) VALUES (10, '2.4.5', 'en', 'Proportion of female employment in mining ', 'Measures the proportion of female, saudi and non-saudi, working in the mining sector.', NULL, 'GASTAT', 'Employment', 'Mining', 0, 'official', 'en', '2026-01-19 11:34:10.326441', '2026-01-19 11:34:10.326441');
INSERT INTO public.indicator_texts (id, indicator_id, language, name, definition, formula, owner, dimension, sector, is_auto_translated, translation_status, source_language, created_at, updated_at) VALUES (11, '2.4.3', 'en', 'Percentage of skilled workforce', 'Indicates the share of skilled workers, impacting operational efficiency and innovation.', NULL, 'Indicator team', 'Employment', 'Mining', 0, 'official', 'en', '2026-01-19 11:34:10.326441', '2026-01-19 11:34:10.326441');
INSERT INTO public.indicator_texts (id, indicator_id, language, name, definition, formula, owner, dimension, sector, is_auto_translated, translation_status, source_language, created_at, updated_at) VALUES (12, '2.6.1', 'en', 'Total investment (growth rates)', 'Represents the variation of total investment in both physical assets (machinery, buildings, and equipment) and intellectual property products (e.g., software, R&D, patents) within the mining sector. This comprehensive measure reflects the sector''s ability to enhance productive capacity, foster innovation, and drive long-term economic growth.', NULL, 'GASTAT', 'Investment', 'Mining', 0, 'official', 'en', '2026-01-19 11:34:10.326441', '2026-01-19 11:34:10.326441');
INSERT INTO public.indicator_texts (id, indicator_id, language, name, definition, formula, owner, dimension, sector, is_auto_translated, translation_status, source_language, created_at, updated_at) VALUES (18, '2.2.2', 'ar', 'القيمة المضافة الإجمالية للتعدين', 'It measures the contribution of the mining sector to a countryâs Gross Domestic Product (GDP). It reflects the economic value generated by mining activities, including the extraction of minerals, oil, and gas, before subtracting intermediate consumption. This indicator is vital for understanding the role of mining in the overall economy, especially in resource-rich countries. A high gross value added indicates a significant contribution of the mining sector to national income, employment, and investment. It also provides insights into productivity trends and helps track the performance of the sector over time. Policymakers use this metric to assess the economic importance of mining, guide resource management strategies, and plan for sustainable development. It can also signal the potential need for diversification in economies where mining dominates, in order to buffer against commodity price volatility and ensure long-term economic stability.', NULL, 'Indicator team', 'الإنتاج', 'Mining', 1, 'official', 'en', '2026-01-19 12:48:04.890465', '2026-01-19 12:48:04.890465');
INSERT INTO public.indicator_texts (id, indicator_id, language, name, definition, formula, owner, dimension, sector, is_auto_translated, translation_status, source_language, created_at, updated_at) VALUES (19, '1.4.2', 'ar', 'التوظيف في قطاع التصنيع للإناث', 'Measures the participation of  women in the manufacturing sector. This helps in understanding gender diversity, workforce inclusion, and the role of women in the industrial labor market.', NULL, 'Indicator team', 'التوظيف', 'Manufacturing', 1, 'official', 'en', '2026-01-19 12:48:04.890465', '2026-01-19 12:48:04.890465');
INSERT INTO public.indicator_texts (id, indicator_id, language, name, definition, formula, owner, dimension, sector, is_auto_translated, translation_status, source_language, created_at, updated_at) VALUES (20, '1.5.2', 'ar', 'إنتاجية العمل (الإنتاج لكل عامل)', 'Labour productivity represents the total volume of output (measured in terms of Gross Domestic Product, GDP) produced per unit of labour (measured in terms of the number of employed persons) during a given time reference period. ', NULL, 'Indicator team', 'التوظيف', 'Manufacturing', 1, 'official', 'en', '2026-01-19 12:48:04.890465', '2026-01-19 12:48:04.890465');
INSERT INTO public.indicator_texts (id, indicator_id, language, name, definition, formula, owner, dimension, sector, is_auto_translated, translation_status, source_language, created_at, updated_at) VALUES (21, '2.4.1', 'ar', 'عدد العاملين في قطاع التعدين', 'Tracks employment levels, providing insights into labor needs and workforce stability.', NULL, 'Indicator team', 'التوظيف', 'Mining', 1, 'official', 'en', '2026-01-19 12:48:04.890465', '2026-01-19 12:48:04.890465');
INSERT INTO public.indicator_texts (id, indicator_id, language, name, definition, formula, owner, dimension, sector, is_auto_translated, translation_status, source_language, created_at, updated_at) VALUES (22, '2.4.5', 'ar', 'نسبة التوظيف النسائي في قطاع التعدين', 'Measures the proportion of female, saudi and non-saudi, working in the mining sector.', NULL, 'GASTAT', 'التوظيف', 'Mining', 1, 'official', 'en', '2026-01-19 12:48:04.890465', '2026-01-19 12:48:04.890465');
INSERT INTO public.indicator_texts (id, indicator_id, language, name, definition, formula, owner, dimension, sector, is_auto_translated, translation_status, source_language, created_at, updated_at) VALUES (23, '2.4.3', 'ar', 'نسبة القوى العاملة المهرة', 'Indicates the share of skilled workers, impacting operational efficiency and innovation.', NULL, 'Indicator team', 'التوظيف', 'Mining', 1, 'official', 'en', '2026-01-19 12:48:04.890465', '2026-01-19 12:48:04.890465');
INSERT INTO public.indicator_texts (id, indicator_id, language, name, definition, formula, owner, dimension, sector, is_auto_translated, translation_status, source_language, created_at, updated_at) VALUES (24, '2.6.1', 'ar', 'إجمالي الاستثمار (معدلات النمو)', 'Represents the variation of total investment in both physical assets (machinery, buildings, and equipment) and intellectual property products (e.g., software, R&D, patents) within the mining sector. This comprehensive measure reflects the sector''s ability to enhance productive capacity, foster innovation, and drive long-term economic growth.', NULL, 'GASTAT', 'الاستثمار', 'Mining', 1, 'official', 'en', '2026-01-19 12:48:04.890465', '2026-01-19 12:48:04.890465');
INSERT INTO public.indicator_texts (id, indicator_id, language, name, definition, formula, owner, dimension, sector, is_auto_translated, translation_status, source_language, created_at, updated_at) VALUES (13, '1.6.1', 'ar', 'إجمالي الاستثمار (معدلات النمو)', 'Represents the variation of total investment in both physical assets (machinery, buildings, and equipment) and intellectual property products (e.g., software, R&D, patents) within the mining sector. This comprehensive measure reflects the sector''s ability to enhance productive capacity, foster innovation, and drive long-term economic growth.', NULL, 'Indicator team', 'الاستثمار', 'Manufacturing', 1, 'official', 'en', '2026-01-19 12:48:04.890465', '2026-01-19 12:48:04.890465');
INSERT INTO public.indicator_texts (id, indicator_id, language, name, definition, formula, owner, dimension, sector, is_auto_translated, translation_status, source_language, created_at, updated_at) VALUES (14, '1.1.3', 'ar', 'القيمة المضافة في التصنيع (MVA)، بالدولار الأمريكي الثابت لعام 2015', 'In consistent with ISIC, MVA measures the net output of manufacturing after adding up all outputs and subtracting intermediate inputs. It is calculated without making deductions for depreciation of fabricated assets or depletion and degradation of natural resources. MVA is a well-recognized and widely used indicator by researchers and policy makers to assess the level of industrialization of a country. This indicator provides a good overview of a countryâs manufacturing size. With the information of manufacturing outputs and intermediate inputs, the overall productivity can also be obtained.', NULL, 'Indicator team', 'الإنتاج', 'Manufacturing', 1, 'official', 'en', '2026-01-19 12:48:04.890465', '2026-01-19 12:48:04.890465');
INSERT INTO public.indicator_texts (id, indicator_id, language, name, definition, formula, owner, dimension, sector, is_auto_translated, translation_status, source_language, created_at, updated_at) VALUES (15, '1.2.1', 'ar', 'معدل نمو القيمة المضافة السنوي', 'This indicator enables trend analysis of manufacturing productivity over time. Fluctuations are therefore able to be identified', NULL, 'Indicator team', 'الإنتاج', 'Manufacturing', 1, 'official', 'en', '2026-01-19 12:48:04.890465', '2026-01-19 12:48:04.890465');
INSERT INTO public.indicator_texts (id, indicator_id, language, name, definition, formula, owner, dimension, sector, is_auto_translated, translation_status, source_language, created_at, updated_at) VALUES (16, '1.7.1', 'ar', 'الصادرات المصنعة لكل موظف', 'This indicator reflects the ability to produce and export of manufacturing. Instead of using the gross population as denominator, the denominator adopted for this indicator is the total number of employees in manufacturing, which is able to readjust the possible difference in the size of manufacturing workforce (as it may be disproportional with total population). This indicator is more effective when conducting international comparisons.', NULL, 'Indicator team', 'الصادرات', 'Manufacturing', 1, 'official', 'en', '2026-01-19 12:48:04.890465', '2026-01-19 12:48:04.890465');
INSERT INTO public.indicator_texts (id, indicator_id, language, name, definition, formula, owner, dimension, sector, is_auto_translated, translation_status, source_language, created_at, updated_at) VALUES (17, '2.5.2', 'ar', 'معدل نمو الأجور في قطاع التعدين', 'Indicates changes in income levels over time, reflecting economic conditions.', NULL, 'GASTAT', 'الأجور', 'Mining', 1, 'official', 'en', '2026-01-19 12:48:04.890465', '2026-01-19 12:48:04.890465');


--
-- Name: indicator_texts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.indicator_texts_id_seq', 24, true);


--
-- Name: indicator_texts indicator_texts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.indicator_texts
    ADD CONSTRAINT indicator_texts_pkey PRIMARY KEY (id);


--
-- Name: indicator_texts uq_indicator_language; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.indicator_texts
    ADD CONSTRAINT uq_indicator_language UNIQUE (indicator_id, language);


--
-- Name: idx_indicator_texts_indicator_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_indicator_texts_indicator_id ON public.indicator_texts USING btree (indicator_id);


--
-- Name: idx_indicator_texts_language; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_indicator_texts_language ON public.indicator_texts USING btree (language);


--
-- Name: indicator_texts indicator_texts_indicator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.indicator_texts
    ADD CONSTRAINT indicator_texts_indicator_id_fkey FOREIGN KEY (indicator_id) REFERENCES public.indicators(id);


--
-- PostgreSQL database dump complete
--

\unrestrict xbfJgmuHdD0uGXbyDHGty3S5T7CDd3PcJHmCfbMIJAUUCyGjKGfs2hpVUIqyrMH

