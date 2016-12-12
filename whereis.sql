--
-- PostgreSQL database dump
--

--
-- Name: checkins; Type: TABLE; Schema: public;

CREATE TABLE "checkins" (
    "id" integer NOT NULL,
    "latitude" "text" NOT NULL,
    "longitude" "text" NOT NULL,
    "display_name" "text",
    "timestamp" bigint NOT NULL,
    "poi_id" bigint
);

CREATE SEQUENCE "checkins_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE "checkins_id_seq" OWNED BY "checkins"."id";

--
-- Name: poi; Type: TABLE; Schema: public; Owner: qgwrkdksjqsezv
--

CREATE TABLE "poi" (
    "id" integer NOT NULL,
    "name" "text" NOT NULL,
    "lat" "text" NOT NULL,
    "lon" "text" NOT NULL,
    "type" "text"
);

CREATE SEQUENCE "poi_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE "poi_id_seq" OWNED BY "poi"."id";


ALTER TABLE ONLY "checkins" ALTER COLUMN "id" SET DEFAULT "nextval"('"checkins_id_seq"'::"regclass");
ALTER TABLE ONLY "poi" ALTER COLUMN "id" SET DEFAULT "nextval"('"poi_id_seq"'::"regclass");

--
-- PostgreSQL database dump complete
--

