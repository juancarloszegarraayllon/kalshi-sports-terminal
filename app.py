import streamlit as st
import pandas as pd
import tempfile
import time
from datetime import date, timedelta, timezone

st.set_page_config(page_title="Kalshi Terminal", layout="wide", page_icon="📡")

st.markdown("""
<style>

html,body,[class*="css"]{font-family:Helvetica,Arial,sans-serif;}
.stApp{background:#0a0a0f;}
section[data-testid="stSidebar"]{background:#0f0f1a!important;border-right:1px solid #1e1e32;}
section[data-testid="stSidebar"] label,section[data-testid="stSidebar"] p{color:#6b7280!important;font-size:11px!important;letter-spacing:.08em;text-transform:uppercase;}
h1{font-family:Helvetica,Arial,sans-serif!important;font-weight:800!important;color:#f0f0ff!important;letter-spacing:-.02em;font-size:2.2rem!important;}
.metric-strip{display:flex;gap:12px;margin-bottom:28px;flex-wrap:wrap;}
.metric-box{background:#0f0f1a;border:1px solid #1e1e32;border-radius:10px;padding:14px 20px;flex:1;min-width:120px;}
.metric-label{font-size:10px;color:#4b5563;text-transform:uppercase;letter-spacing:.1em;margin-bottom:4px;}
.metric-value{font-size:22px;font-weight:500;color:#a5b4fc;}
.card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px;}
.market-card{background:#0f0f1a;border:1px solid #1e1e32;border-radius:12px;padding:18px 20px;transition:border-color .2s,transform .15s;}
.market-card:hover{border-color:#4f46e5;transform:translateY(-2px);}
.card-top{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;}
.cat-pill{font-size:10px;font-weight:500;letter-spacing:.08em;text-transform:uppercase;padding:3px 10px;border-radius:4px;border:1px solid;white-space:nowrap;}
.pill-sports{background:#1a2e1a;color:#4ade80;border-color:#166534;}
.pill-elections{background:#2e1a1e;color:#f472b6;border-color:#9d174d;}
.pill-politics{background:#1e1a2e;color:#818cf8;border-color:#3730a3;}
.pill-economics{background:#2e2a1a;color:#fbbf24;border-color:#92400e;}
.pill-financials{background:#2e2a1a;color:#fb923c;border-color:#9a3412;}
.pill-crypto{background:#1e2a2e;color:#67e8f9;border-color:#0e7490;}
.pill-companies{background:#2e1e2e;color:#d8b4fe;border-color:#7e22ce;}
.pill-entertainment{background:#2e1e1a;color:#fdba74;border-color:#c2410c;}
.pill-climate{background:#1a2e2e;color:#22d3ee;border-color:#164e63;}
.pill-science{background:#1e2e1a;color:#86efac;border-color:#14532d;}
.pill-health{background:#2e1a2e;color:#e879f9;border-color:#701a75;}
.pill-default{background:#1e1e32;color:#94a3b8;border-color:#2d2d55;}
.date-text{font-size:11px;color:#6b7280;}.begins-text{font-size:11px;color:#10b981;font-weight:600;}.live-text{font-size:11px;color:#10b981;font-weight:700;letter-spacing:.02em;}.date-text{font-size:11px;color:#6b7280;}.card-timing{display:flex;flex-direction:row;align-items:center;gap:2px;flex-wrap:wrap;margin-bottom:8px;}.card-dates{display:flex;flex-direction:row;align-items:center;gap:2px;}
.card-icon{font-size:20px;margin-bottom:6px;display:block;}
.card-title{font-size:14px;font-weight:500;color:#e2e8f0;line-height:1.45;margin-bottom:12px;min-height:58px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;}
.card-footer{border-top:1px solid #1a1a2e;padding-top:10px;}
.ticker-text{font-size:10px;color:#374151;letter-spacing:.04em;display:block;margin-bottom:8px;word-break:break-all;}
.odds-row{display:flex;gap:8px;}
.odds-yes{flex:1;background:#0d2d1a;border:1px solid #166534;border-radius:6px;padding:5px 8px;text-align:center;}
.odds-no{flex:1;background:#2d0d0d;border:1px solid #7f1d1d;border-radius:6px;padding:5px 8px;text-align:center;}
.outcome-row{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:6px;}
.outcome-label{font-size:11px;color:#9ca3af;font-weight:500;flex:0 0 auto;min-width:80px;max-width:140px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.outcome-chance{font-size:13px;font-weight:600;color:#e2e8f0;flex:0 0 auto;min-width:38px;text-align:right;}
.outcome-odds{display:flex;gap:6px;flex:1;justify-content:flex-end;}
.outcome-odds .odds-yes,.outcome-odds .odds-no{flex:0 0 auto;min-width:52px;}
.ticker-link{font-size:10px;color:#4f46e5;letter-spacing:.04em;display:block;margin-bottom:8px;word-break:break-all;text-decoration:none;}
.ticker-link:hover{color:#818cf8;text-decoration:underline;}
.odds-label{font-size:9px;color:#6b7280;text-transform:uppercase;letter-spacing:.08em;}
.odds-price-yes{font-size:15px;font-weight:500;color:#4ade80;}
.odds-price-no{font-size:15px;font-weight:500;color:#f87171;}
.empty-state{text-align:center;padding:80px 20px;color:#374151;font-size:14px;}
hr{border-color:#1e1e32!important;}
.stTabs [data-baseweb="tab-list"]{background:#0f0f1a;border-bottom:1px solid #1e1e32;gap:2px;flex-wrap:wrap;}
.stTabs [data-baseweb="tab"]{background:transparent;color:#4b5563;border:none;font-size:12px;padding:8px 12px;}
.stTabs [aria-selected="true"]{background:#1e1e32!important;color:#a5b4fc!important;border-radius:6px 6px 0 0;}
</style>
""", unsafe_allow_html=True)

UTC = timezone.utc

# ── Category metadata ─────────────────────────────────────────────────────────
TOP_CATS = ["Sports","Elections","Politics","Economics","Financials",
            "Crypto","Companies","Entertainment","Climate and Weather",
            "Science and Technology","Health","Social","World","Transportation","Mentions"]

CAT_META = {
    "Sports":("🏟️","pill-sports"),"Elections":("🗳️","pill-elections"),
    "Politics":("🏛️","pill-politics"),"Economics":("📈","pill-economics"),
    "Financials":("💰","pill-financials"),"Crypto":("₿","pill-crypto"),
    "Companies":("🏢","pill-companies"),"Entertainment":("🎬","pill-entertainment"),
    "Climate and Weather":("🌍","pill-climate"),"Science and Technology":("🔬","pill-science"),
    "Health":("🏥","pill-health"),"Social":("👥","pill-default"),
    "World":("🌐","pill-default"),"Transportation":("✈️","pill-default"),
    "Mentions":("💬","pill-default"),
}

CAT_TAGS = {
    "Elections":["US Elections","International","House","Senate","Primaries","Governor"],
    "Politics":["Trump","Congress","International","SCOTUS","Local","Tariffs"],
    "Economics":["Fed","Inflation","GDP","Jobs","Housing","Oil","Global"],
    "Financials":["S&P","Nasdaq","Metals","Agriculture","Oil & Gas","Treasuries"],
    "Crypto":["BTC","ETH","SOL","DOGE","XRP","BNB"],
    "Companies":["IPOs","Elon Musk","CEOs","Tech","Layoffs"],
    "Entertainment":["Music","Television","Movies","Awards","Video games"],
    "Climate and Weather":["Hurricanes","Temperature","Snow and rain","Climate change"],
    "Science and Technology":["AI","Space","Medicine","Energy"],
}

# ── SPORT_SERIES: built from 594 live series (ground truth from CSV) ──────────
# series_ticker → sport name
SERIES_SPORT = {}

_SPORT_SERIES = {
    "Soccer": [
        "KXEPLGAME","KXEPL1H","KXEPLSPREAD","KXEPLTOTAL","KXEPLBTTS",
        "KXEPLTOP4","KXEPLTOP2","KXEPLTOP6","KXEPLRELEGATION","KXPREMIERLEAGUE",
        "KXARSENALCUPS","KXWINSTREAKMANU","KXNEXTMANAGERMANU","KXPFAPOY","KXLAMINEYAMAL",
        "KXUCLGAME","KXUCL1H","KXUCLSPREAD","KXUCLTOTAL","KXUCLBTTS","KXUCL",
        "KXUCLFINALIST","KXUCLRO4","KXUCLW","KXLEADERUCLGOALS","KXTEAMSINUCL",
        "KXUELGAME","KXUELSPREAD","KXUELTOTAL","KXUEL",
        "KXUECL","KXUECLGAME",
        "KXLALIGAGAME","KXLALIGA1H","KXLALIGASPREAD","KXLALIGATOTAL","KXLALIGABTTS",
        "KXLALIGA","KXLALIGATOP4","KXLALIGARELEGATION",
        "KXLALIGA2GAME",
        "KXSERIEAGAME","KXSERIEA1H","KXSERIEASPREAD","KXSERIEATOTAL","KXSERIEABTTS",
        "KXSERIEA","KXSERIEATOP4","KXSERIEARELEGATION",
        "KXSERIEBGAME",
        "KXBUNDESLIGAGAME","KXBUNDESLIGA1H","KXBUNDESLIGASPREAD","KXBUNDESLIGATOTAL",
        "KXBUNDESLIGABTTS","KXBUNDESLIGA","KXBUNDESLIGATOP4","KXBUNDESLIGARELEGATION",
        "KXBUNDESLIGA2GAME",
        "KXLIGUE1GAME","KXLIGUE11H","KXLIGUE1SPREAD","KXLIGUE1TOTAL","KXLIGUE1BTTS",
        "KXLIGUE1","KXLIGUE1TOP4","KXLIGUE1RELEGATION",
        "KXMLSGAME","KXMLSSPREAD","KXMLSTOTAL","KXMLSBTTS","KXMLSCUP","KXMLSEAST","KXMLSWEST",
        "KXLIGAMXGAME","KXLIGAMXSPREAD","KXLIGAMXTOTAL","KXLIGAMX",
        "KXBRASILEIROGAME","KXBRASILEIROSPREAD","KXBRASILEIROTOTAL","KXBRASILEIRO","KXBRASILEIROTOPX",
        "KXWCGAME","KXWCROUND","KXWCGROUPWIN","KXWCGROUPQUAL","KXWCGOALLEADER",
        "KXWCMESSIRONALDO","KXWCLOCATION","KXWCIRAN","KXWCSQUAD","KXMENWORLDCUP",
        "KXSOCCERPLAYMESSI","KXSOCCERPLAYCRON","KXFIFAUSPULL","KXFIFAUSPULLGAME",
        "KXSAUDIPLGAME","KXSAUDIPLSPREAD","KXSAUDIPLTOTAL",
        "KXLIGAPORTUGALGAME","KXLIGAPORTUGAL",
        "KXEREDIVISIEGAME","KXEREDIVISIE",
        "KXCOPADELREY","KXDFBPOKAL","KXFACUP","KXCOPPAITALIA",
        "KXEFLCHAMPIONSHIPGAME","KXEFLCHAMPIONSHIP","KXEFLPROMO",
        "KXSUPERLIGGAME","KXSUPERLIG",
        "KXCONCACAFCCUPGAME","KXCONMEBOLLIBGAME","KXCONMEBOLSUDGAME",
        "KXUSLGAME","KXUSL",
        "KXSCOTTISHPREMGAME",
        "KXEKSTRAKLASAGAME","KXEKSTRAKLASA",
        "KXALEAGUEGAME","KXALEAGUESPREAD","KXALEAGUETOTAL",
        "KXKLEAGUEGAME","KXKLEAGUE",
        "KXJLEAGUEGAME",
        "KXCHNSLGAME","KXCHNSL",
        "KXALLSVENSKANGAME",
        "KXDENSUPERLIGAGAME","KXDENSUPERLIGA",
        "KXSWISSLEAGUEGAME",
        "KXARGPREMDIVGAME",
        "KXDIMAYORGAME",
        "KXURYPDGAME","KXURYPD",
        "KXECULPGAME","KXECULP",
        "KXVENFUTVEGAME","KXVENFUTVE",
        "KXCHLLDPGAME","KXCHLLDP",
        "KXAPFDDHGAME","KXAPFDDH",
        "KXBALLERLEAGUEGAME",
        "KXSLGREECE",
        "KXTHAIL1GAME","KXTHAIL1",
        "KXEGYPLGAME",
        "KXHNLGAME",
        "KXBELGIANPLGAME","KXBELGIANPL",
        "KXPERLIGA1",
        "KXKNVBCUP",
        "KXSOCCERTRANSFER","KXJOINLEAGUE","KXJOINRONALDO","KXJOINCLUB","KXBALLONDOR",
    ],
    "Basketball": [
        "KXNBAGAME","KXNBASPREAD","KXNBATOTAL","KXNBATEAMTOTAL",
        "KXNBA1HWINNER","KXNBA1HSPREAD","KXNBA1HTOTAL",
        "KXNBA2HWINNER","KXNBA2D","KXNBA3D","KXNBA3PT",
        "KXNBAPTS","KXNBAREB","KXNBAAST","KXNBABLK","KXNBASTL",
        "KXNBA","KXNBAEAST","KXNBAWEST","KXNBAPLAYOFF","KXNBAPLAYIN",
        "KXNBAATLANTIC","KXNBACENTRAL","KXNBASOUTHEAST",
        "KXNBANORTHWEST","KXNBAPACIFIC","KXNBASOUTHWEST",
        "KXNBAEAST1SEED","KXNBAWEST1SEED",
        "KXTEAMSINNBAF","KXTEAMSINNBAEF","KXTEAMSINNBAWF",
        "KXNBAMATCHUP","KXNBAWINS","KXRECORDNBABEST",
        "KXNBAMVP","KXNBAROY","KXNBACOY","KXNBADPOY","KXNBASIXTH",
        "KXNBAMIMP","KXNBACLUTCH","KXNBAFINMVP","KXNBAWFINMVP","KXNBAEFINMVP",
        "KXNBA1STTEAM","KXNBA2NDTEAM","KXNBA3RDTEAM",
        "KXNBA1STTEAMDEF","KXNBA2NDTEAMDEF",
        "KXLEADERNBAPTS","KXLEADERNBAREB","KXLEADERNBAAST",
        "KXLEADERNBABLK","KXLEADERNBASTL","KXLEADERNBA3PT",
        "KXNBADRAFT1","KXNBADRAFTPICK","KXNBADRAFTTOP","KXNBADRAFTCAT","KXNBADRAFTCOMP",
        "KXNBATOPPICK","KXNBALOTTERYODDS","KXNBATOP5ROTY",
        "KXNBATEAM","KXNBASEATTLE","KXCITYNBAEXPAND","KXSONICS",
        "KXNEXTTEAMNBA","KXLBJRETIRE","KXSPORTSOWNERLBJ","KXSTEPHDEAL",
        "KXQUADRUPLEDOUBLE","KXSHAI20PTREC","KXNBA2KCOVER",
        "KXWNBADRAFT1","KXWNBADRAFTTOP3","KXWNBADELAY","KXWNBAGAMESPLAYED",
        "KXMARMAD","KXNCAAMBNEXTCOACH",
        "KXEUROLEAGUEGAME","KXBSLGAME","KXBBLGAME","KXACBGAME",
        "KXISLGAME","KXABAGAME","KXCBAGAME","KXBBSERIEAGAME",
        "KXJBLEAGUEGAME","KXLNBELITEGAME","KXARGLNBGAME","KXVTBGAME",
    ],
    "Baseball": [
        "KXMLBGAME","KXMLBRFI","KXMLBSPREAD","KXMLBTOTAL","KXMLBTEAMTOTAL",
        "KXMLBF5","KXMLBF5SPREAD","KXMLBF5TOTAL",
        "KXMLBHIT","KXMLBHR","KXMLBHRR","KXMLBKS","KXMLBTB",
        "KXMLB","KXMLBAL","KXMLBNL",
        "KXMLBALEAST","KXMLBALWEST","KXMLBALCENT",
        "KXMLBNLEAST","KXMLBNLWEST","KXMLBNLCENT",
        "KXMLBPLAYOFFS","KXTEAMSINWS",
        "KXMLBBESTRECORD","KXMLBWORSTRECORD","KXMLBLSTREAK","KXMLBWSTREAK",
        "KXMLBWINS-ATH","KXMLBWINS-ATL","KXMLBWINS-AZ","KXMLBWINS-BAL",
        "KXMLBWINS-BOS","KXMLBWINS-CHC","KXMLBWINS-CIN","KXMLBWINS-CLE",
        "KXMLBWINS-COL","KXMLBWINS-CWS","KXMLBWINS-DET","KXMLBWINS-HOU",
        "KXMLBWINS-KC","KXMLBWINS-LAA","KXMLBWINS-LAD","KXMLBWINS-MIA",
        "KXMLBWINS-MIL","KXMLBWINS-MIN","KXMLBWINS-NYM","KXMLBWINS-NYY",
        "KXMLBWINS-PHI","KXMLBWINS-PIT","KXMLBWINS-SD","KXMLBWINS-SEA",
        "KXMLBWINS-SF","KXMLBWINS-STL","KXMLBWINS-TB","KXMLBWINS-TEX",
        "KXMLBWINS-TOR","KXMLBWINS-WSH",
        "KXMLBALMVP","KXMLBNLMVP","KXMLBALCY","KXMLBNLCY",
        "KXMLBALROTY","KXMLBNLROTY","KXMLBEOTY","KXMLBALMOTY","KXMLBNLMOTY",
        "KXMLBALHAARON","KXMLBNLHAARON","KXMLBALCPOTY","KXMLBNLCPOTY",
        "KXMLBALRELOTY","KXMLBNLRELOTY",
        "KXMLBSTAT","KXMLBSTATCOUNT","KXMLBSEASONHR",
        "KXLEADERMLBAVG","KXLEADERMLBDOUBLES","KXLEADERMLBERA",
        "KXLEADERMLBHITS","KXLEADERMLBHR","KXLEADERMLBKS","KXLEADERMLBOPS",
        "KXLEADERMLBRBI","KXLEADERMLBRUNS","KXLEADERMLBSTEALS",
        "KXLEADERMLBTRIPLES","KXLEADERMLBWAR","KXLEADERMLBWINS",
        "KXMLBTRADE","KXWSOPENTRANTS",
        "KXNPBGAME","KXKBOGAME","KXNCAABBGAME",
        "KXNCAABASEBALL","KXNCAABBGS",
    ],
    "Football": [
        "KXUFLGAME",
        "KXSB","KXNFLPLAYOFF","KXNFLAFCCHAMP","KXNFLNFCCHAMP",
        "KXNFLAFCEAST","KXNFLAFCWEST","KXNFLAFCNORTH","KXNFLAFCSOUTH",
        "KXNFLNFCEAST","KXNFLNFCWEST","KXNFLNFCNORTH","KXNFLNFCSOUTH",
        "KXNFLMVP","KXNFLOPOTY","KXNFLDPOTY","KXNFLOROTY","KXNFLDROTY","KXNFLCOTY",
        "KXNFLDRAFT1","KXNFLDRAFT1ST","KXNFLDRAFTPICK","KXNFLDRAFTTOP",
        "KXNFLDRAFTWR","KXNFLDRAFTDB","KXNFLDRAFTTE","KXNFLDRAFTQB",
        "KXNFLDRAFTOL","KXNFLDRAFTEDGE","KXNFLDRAFTLB","KXNFLDRAFTRB",
        "KXNFLDRAFTDT","KXNFLDRAFTTEAM",
        "KXLEADERNFLSACKS","KXLEADERNFLINT","KXLEADERNFLPINT",
        "KXLEADERNFLPTDS","KXLEADERNFLPYDS","KXLEADERNFLRTDS",
        "KXLEADERNFLRUSHTDS","KXLEADERNFLRUSHYDS","KXLEADERNFLRYDS",
        "KXNFLTEAM1POS","KXNFLPRIMETIME","KXNFLTRADE","KXNEXTTEAMNFL",
        "KXRECORDNFLBEST","KXRECORDNFLWORST",
        "KXKELCERETIRE","KXSTARTINGQBWEEK1","KXCOACHOUTNFL","KXCOACHOUTNCAAFB",
        "KXARODGRETIRE","KXRELOCATIONCHI","KX1STHOMEGAME","KXSORONDO",
        "KXNCAAF","KXHEISMAN","KXNCAAFCONF","KXNCAAFACC","KXNCAAFB10","KXNCAAFB12",
        "KXNCAAFSEC","KXNCAAFAAC","KXNCAAFSBELT","KXNCAAFMWC","KXNCAAFMAC",
        "KXNCAAFCUSA","KXNCAAFPAC12","KXNCAAFPLAYOFF","KXNCAAFFINALIST",
        "KXNCAAFUNDEFEATED","KXNCAAFCOTY","KXNCAAFAPRANK",
        "KXNDJOINCONF","KXCOVEREA","KXDONATEMRBEAST",
    ],
    "Hockey": [
        "KXNHLGAME","KXNHLSPREAD","KXNHLTOTAL","KXNHL",
        "KXNHLPLAYOFF","KXTEAMSINSC","KXNHLPRES",
        "KXNHLEAST","KXNHLWEST","KXNHLADAMS","KXNHLCENTRAL",
        "KXNHLATLANTIC","KXNHLMETROPOLITAN","KXNHLPACIFIC",
        "KXNHLHART","KXNHLNORRIS","KXNHLVEZINA","KXNHLCALDER",
        "KXNHLROSS","KXNHLRICHARD",
        "KXAHLGAME","KXCANADACUP","KXNCAAHOCKEY","KXNCAAHOCKEYGAME",
        "KXKHLGAME","KXSHLGAME","KXLIIGAGAME","KXELHGAME","KXNLGAME","KXDELGAME",
    ],
    "Tennis": [
        "KXATPMATCH","KXATPSETWINNER","KXATPCHALLENGERMATCH",
        "KXATPGRANDSLAM","KXATPGRANDSLAMFIELD","KXATP1RANK",
        "KXMCMMEN","KXFOMEN",
        "KXWTAMATCH","KXWTAGRANDSLAM","KXWTASERENA","KXFOWOMEN",
        "KXGRANDSLAM","KXGRANDSLAMJFONSECA","KXGOLFTENNISMAJORS",
    ],
    "Golf": [
        "KXPGATOUR","KXPGAH2H","KXPGA3BALL","KXPGA5BALL",
        "KXPGAR1LEAD","KXPGAR1TOP5","KXPGAR1TOP10","KXPGAR1TOP20",
        "KXPGAR2LEAD","KXPGAR2TOP5","KXPGAR2TOP10",
        "KXPGAR3LEAD","KXPGAR3TOP5","KXPGAR3TOP10",
        "KXPGATOP5","KXPGATOP10","KXPGATOP20","KXPGATOP40",
        "KXPGAPLAYOFF","KXPGACUTLINE","KXPGAMAKECUT","KXPGAAGECUT",
        "KXPGAWINNERREGION","KXPGALOWSCORE","KXPGASTROKEMARGIN","KXPGAWINNINGSCORE",
        "KXPGAPLAYERCAT","KXPGABIRDIES","KXPGAROUNDSCORE",
        "KXPGAEAGLE","KXPGAHOLEINONE","KXPGABOGEYFREE",
        "KXPGAMAJORTOP10","KXPGAMAJORWIN","KXPGAMASTERS",
        "KXGOLFMAJORS","KXGOLFTENNISMAJORS",
        "KXPGARYDER","KXPGASOLHEIM","KXRYDERCUPCAPTAIN",
        "KXPGACURRY","KXPGATIGER","KXBRYSONCOURSERECORDS","KXSCOTTIESLAM",
    ],
    "MMA": [
        "KXUFCFIGHT",
        "KXUFCHEAVYWEIGHTTITLE","KXUFCLHEAVYWEIGHTTITLE","KXUFCMIDDLEWEIGHTTITLE",
        "KXUFCWELTERWEIGHTTITLE","KXUFCLIGHTWEIGHTTITLE","KXUFCFEATHERWEIGHTTITLE",
        "KXUFCBANTAMWEIGHTTITLE","KXUFCFLYWEIGHTTITLE",
        "KXMCGREGORFIGHTNEXT","KXCARDPRESENCEUFCWH","KXUFCWHITEHOUSE",
    ],
    "Cricket": [
        "KXIPLGAME","KXIPL","KXIPLFOUR","KXIPLSIX","KXIPLTEAMTOTAL",
        "KXPSLGAME","KXPSL","KXT20MATCH",
    ],
    "Esports": [
        "KXVALORANTMAP","KXVALORANTGAME",
        "KXLOLGAME","KXLOLMAP","KXLOLTOTALMAPS",
        "KXR6GAME",
        "KXCS2GAME","KXCS2MAP","KXCS2TOTALMAPS",
        "KXDOTA2GAME","KXDOTA2MAP",
        "KXOWGAME",
    ],
    "Motorsport": [
        "KXF1RACE","KXF1RACEPODIUM","KXF1TOP5","KXF1TOP10","KXF1FASTLAP",
        "KXF1CONSTRUCTORS","KXF1RETIRE","KXF1","KXF1OCCUR","KXF1CHINA",
        "KXNASCARCUPSERIES","KXNASCARRACE","KXNASCARTOP3","KXNASCARTOP5",
        "KXNASCARTOP10","KXNASCARTOP20","KXNASCARTRUCKSERIES","KXNASCARAUTOPARTSSERIES",
        "KXMOTOGP","KXMOTOGPTEAMS",
        "KXINDYCARSERIES",
    ],
    "Boxing": [
        "KXBOXING","KXFLOYDTYSONFIGHT",
        "KXWBCHEAVYWEIGHTTITLE","KXWBCCRUISERWEIGHTTITLE","KXWBCMIDDLEWEIGHTTITLE",
        "KXWBCWELTERWEIGHTTITLE","KXWBCLIGHTWEIGHTTITLE","KXWBCFEATHERWEIGHTTITLE",
        "KXWBCBANTAMWEIGHTTITLE","KXWBCFLYWEIGHTTITLE",
    ],
    "Rugby": [
        "KXRUGBYNRLMATCH","KXNRLCHAMP",
        "KXPREMCHAMP","KXSLRCHAMP","KXFRA14CHAMP",
    ],
    "Lacrosse": [
        "KXNCAAMLAXGAME","KXNCAALAXFINAL","KXLAXTEWAARATON",
    ],
    "Chess": ["KXCHESSWORLDCHAMPION","KXCHESSCANDIDATES"],
    "Darts":  ["KXDARTSMATCH","KXPREMDARTS"],
    "Aussie Rules": ["KXAFLGAME"],
    "Other Sports": [
        "KXSAILGP","KXPIZZASCORE9","KXROCKANDROLLHALLOFFAME",
        "KXEUROVISIONISRAELBAN","KXCOLLEGEGAMEDAYGUEST","KXWSOPENTRANTS",
    ],
}

SPORT_ICONS = {
    "Soccer":"⚽","Basketball":"🏀","Baseball":"⚾","Football":"🏈",
    "Hockey":"🏒","Tennis":"🎾","Golf":"⛳","MMA":"🥊","Cricket":"🏏",
    "Esports":"🎮","Motorsport":"🏎️","Boxing":"🥊","Rugby":"🏉",
    "Lacrosse":"🥍","Chess":"♟️","Darts":"🎯","Aussie Rules":"🏉",
    "Other Sports":"🏆",
}

for sport, series_list in _SPORT_SERIES.items():
    for s in series_list:
        SERIES_SPORT[s] = sport

def get_sport(series_ticker):
    return SERIES_SPORT.get(str(series_ticker).upper(), "")

# ── Soccer competition mapping (from ground truth) ────────────────────────────
SOCCER_COMP = {
    "KXEPLGAME":"EPL","KXEPL1H":"EPL","KXEPLSPREAD":"EPL","KXEPLTOTAL":"EPL",
    "KXEPLBTTS":"EPL","KXEPLTOP4":"EPL","KXEPLTOP2":"EPL","KXEPLTOP6":"EPL",
    "KXEPLRELEGATION":"EPL","KXPREMIERLEAGUE":"EPL","KXARSENALCUPS":"EPL",
    "KXWINSTREAKMANU":"EPL","KXNEXTMANAGERMANU":"EPL","KXPFAPOY":"EPL","KXLAMINEYAMAL":"EPL",
    "KXUCLGAME":"Champions League","KXUCL1H":"Champions League","KXUCLSPREAD":"Champions League",
    "KXUCLTOTAL":"Champions League","KXUCLBTTS":"Champions League","KXUCL":"Champions League",
    "KXUCLFINALIST":"Champions League","KXUCLRO4":"Champions League","KXUCLW":"Champions League",
    "KXLEADERUCLGOALS":"Champions League","KXTEAMSINUCL":"Champions League",
    "KXUELGAME":"Europa League","KXUELSPREAD":"Europa League","KXUELTOTAL":"Europa League","KXUEL":"Europa League",
    "KXUECL":"Conference League","KXUECLGAME":"Conference League",
    "KXLALIGAGAME":"La Liga","KXLALIGA1H":"La Liga","KXLALIGASPREAD":"La Liga",
    "KXLALIGATOTAL":"La Liga","KXLALIGABTTS":"La Liga","KXLALIGA":"La Liga",
    "KXLALIGATOP4":"La Liga","KXLALIGARELEGATION":"La Liga",
    "KXLALIGA2GAME":"La Liga 2",
    "KXSERIEAGAME":"Serie A","KXSERIEA1H":"Serie A","KXSERIEASPREAD":"Serie A",
    "KXSERIEATOTAL":"Serie A","KXSERIEABTTS":"Serie A","KXSERIEA":"Serie A",
    "KXSERIEATOP4":"Serie A","KXSERIEARELEGATION":"Serie A",
    "KXSERIEBGAME":"Serie B",
    "KXBUNDESLIGAGAME":"Bundesliga","KXBUNDESLIGA1H":"Bundesliga","KXBUNDESLIGASPREAD":"Bundesliga",
    "KXBUNDESLIGATOTAL":"Bundesliga","KXBUNDESLIGABTTS":"Bundesliga","KXBUNDESLIGA":"Bundesliga",
    "KXBUNDESLIGATOP4":"Bundesliga","KXBUNDESLIGARELEGATION":"Bundesliga",
    "KXBUNDESLIGA2GAME":"Bundesliga 2",
    "KXLIGUE1GAME":"Ligue 1","KXLIGUE11H":"Ligue 1","KXLIGUE1SPREAD":"Ligue 1",
    "KXLIGUE1TOTAL":"Ligue 1","KXLIGUE1BTTS":"Ligue 1","KXLIGUE1":"Ligue 1",
    "KXLIGUE1TOP4":"Ligue 1","KXLIGUE1RELEGATION":"Ligue 1",
    "KXMLSGAME":"MLS","KXMLSSPREAD":"MLS","KXMLSTOTAL":"MLS","KXMLSBTTS":"MLS",
    "KXMLSCUP":"MLS","KXMLSEAST":"MLS","KXMLSWEST":"MLS",
    "KXLIGAMXGAME":"Liga MX","KXLIGAMXSPREAD":"Liga MX","KXLIGAMXTOTAL":"Liga MX","KXLIGAMX":"Liga MX",
    "KXBRASILEIROGAME":"Brasileiro","KXBRASILEIROSPREAD":"Brasileiro",
    "KXBRASILEIROTOTAL":"Brasileiro","KXBRASILEIRO":"Brasileiro","KXBRASILEIROTOPX":"Brasileiro",
    "KXWCGAME":"World Cup","KXWCROUND":"World Cup","KXWCGROUPWIN":"World Cup",
    "KXWCGROUPQUAL":"World Cup","KXWCGOALLEADER":"World Cup","KXWCMESSIRONALDO":"World Cup",
    "KXWCLOCATION":"World Cup","KXWCIRAN":"World Cup","KXWCSQUAD":"World Cup",
    "KXMENWORLDCUP":"World Cup","KXSOCCERPLAYMESSI":"World Cup","KXSOCCERPLAYCRON":"World Cup",
    "KXFIFAUSPULL":"World Cup","KXFIFAUSPULLGAME":"World Cup",
    "KXSAUDIPLGAME":"Saudi Pro League","KXSAUDIPLSPREAD":"Saudi Pro League","KXSAUDIPLTOTAL":"Saudi Pro League",
    "KXLIGAPORTUGALGAME":"Liga Portugal","KXLIGAPORTUGAL":"Liga Portugal",
    "KXEREDIVISIEGAME":"Eredivisie","KXEREDIVISIE":"Eredivisie",
    "KXCOPADELREY":"Copa del Rey","KXDFBPOKAL":"DFB Pokal",
    "KXFACUP":"FA Cup","KXCOPPAITALIA":"Coppa Italia",
    "KXEFLCHAMPIONSHIPGAME":"EFL Championship","KXEFLCHAMPIONSHIP":"EFL Championship","KXEFLPROMO":"EFL Championship",
    "KXSUPERLIGGAME":"Super Lig","KXSUPERLIG":"Super Lig",
    "KXCONCACAFCCUPGAME":"CONCACAF",
    "KXCONMEBOLLIBGAME":"Libertadores","KXCONMEBOLSUDGAME":"Copa Sudamericana",
    "KXUSLGAME":"USL","KXUSL":"USL",
    "KXSCOTTISHPREMGAME":"Scottish Prem",
    "KXEKSTRAKLASAGAME":"Ekstraklasa","KXEKSTRAKLASA":"Ekstraklasa",
    "KXALEAGUEGAME":"A-League","KXALEAGUESPREAD":"A-League","KXALEAGUETOTAL":"A-League",
    "KXKLEAGUEGAME":"K League","KXKLEAGUE":"K League",
    "KXJLEAGUEGAME":"J League",
    "KXCHNSLGAME":"Chinese SL","KXCHNSL":"Chinese SL",
    "KXALLSVENSKANGAME":"Allsvenskan",
    "KXDENSUPERLIGAGAME":"Danish SL","KXDENSUPERLIGA":"Danish SL",
    "KXSWISSLEAGUEGAME":"Swiss League",
    "KXARGPREMDIVGAME":"Argentinian Div","KXDIMAYORGAME":"Colombian Div",
    "KXURYPDGAME":"Uruguayan Div","KXURYPD":"Uruguayan Div",
    "KXECULPGAME":"Ecuador LigaPro","KXECULP":"Ecuador LigaPro",
    "KXVENFUTVEGAME":"Venezuelan Div","KXVENFUTVE":"Venezuelan Div",
    "KXCHLLDPGAME":"Chilean Div","KXCHLLDP":"Chilean Div",
    "KXAPFDDHGAME":"APF Paraguay","KXAPFDDH":"APF Paraguay",
    "KXBALLERLEAGUEGAME":"Baller League",
    "KXSLGREECE":"Greek SL",
    "KXTHAIL1GAME":"Thai League","KXTHAIL1":"Thai League",
    "KXEGYPLGAME":"Egyptian PL",
    "KXHNLGAME":"HNL Croatia",
    "KXBELGIANPLGAME":"Belgian Pro","KXBELGIANPL":"Belgian Pro",
    "KXPERLIGA1":"Peruvian L1","KXKNVBCUP":"KNVB Cup",
    "KXSOCCERTRANSFER":"Transfers/News","KXJOINLEAGUE":"Transfers/News",
    "KXJOINRONALDO":"Transfers/News","KXJOINCLUB":"Transfers/News","KXBALLONDOR":"Transfers/News",
}

# ── Sport sub-tabs (series-based, not keyword-based) ─────────────────────────
SPORT_SUBTABS = {
    "Basketball": [
        ("NBA Games",    ["KXNBAGAME","KXNBASPREAD","KXNBATOTAL","KXNBATEAMTOTAL",
                          "KXNBA1HWINNER","KXNBA1HSPREAD","KXNBA1HTOTAL","KXNBA2HWINNER",
                          "KXNBA2D","KXNBA3D","KXNBA3PT","KXNBAPTS","KXNBAREB",
                          "KXNBAAST","KXNBABLK","KXNBASTL"]),
        ("NBA Season",   ["KXNBA","KXNBAEAST","KXNBAWEST","KXNBAPLAYOFF","KXNBAPLAYIN",
                          "KXNBAATLANTIC","KXNBACENTRAL","KXNBASOUTHEAST","KXNBANORTHWEST",
                          "KXNBAPACIFIC","KXNBASOUTHWEST","KXNBAEAST1SEED","KXNBAWEST1SEED",
                          "KXTEAMSINNBAF","KXTEAMSINNBAEF","KXTEAMSINNBAWF",
                          "KXNBAMATCHUP","KXNBAWINS","KXRECORDNBABEST"]),
        ("NBA Awards",   ["KXNBAMVP","KXNBAROY","KXNBACOY","KXNBADPOY","KXNBASIXTH",
                          "KXNBAMIMP","KXNBACLUTCH","KXNBAFINMVP","KXNBAWFINMVP","KXNBAEFINMVP",
                          "KXNBA1STTEAM","KXNBA2NDTEAM","KXNBA3RDTEAM",
                          "KXNBA1STTEAMDEF","KXNBA2NDTEAMDEF"]),
        ("NBA Stats",    ["KXLEADERNBAPTS","KXLEADERNBAREB","KXLEADERNBAAST",
                          "KXLEADERNBABLK","KXLEADERNBASTL","KXLEADERNBA3PT"]),
        ("NBA Draft",    ["KXNBADRAFT1","KXNBADRAFTPICK","KXNBADRAFTTOP","KXNBADRAFTCAT",
                          "KXNBADRAFTCOMP","KXNBATOPPICK","KXNBALOTTERYODDS","KXNBATOP5ROTY"]),
        ("NBA Other",    ["KXNBATEAM","KXNBASEATTLE","KXCITYNBAEXPAND","KXSONICS",
                          "KXNEXTTEAMNBA","KXLBJRETIRE","KXSPORTSOWNERLBJ","KXSTEPHDEAL",
                          "KXQUADRUPLEDOUBLE","KXSHAI20PTREC","KXNBA2KCOVER"]),
        ("WNBA",         ["KXWNBADRAFT1","KXWNBADRAFTTOP3","KXWNBADELAY","KXWNBAGAMESPLAYED"]),
        ("NCAAB",        ["KXMARMAD","KXNCAAMBNEXTCOACH"]),
        ("International",["KXEUROLEAGUEGAME","KXBSLGAME","KXBBLGAME","KXACBGAME",
                          "KXISLGAME","KXABAGAME","KXCBAGAME","KXBBSERIEAGAME",
                          "KXJBLEAGUEGAME","KXLNBELITEGAME","KXARGLNBGAME","KXVTBGAME"]),
    ],
    "Baseball": [
        ("MLB Games",    ["KXMLBGAME","KXMLBRFI","KXMLBSPREAD","KXMLBTOTAL","KXMLBTEAMTOTAL",
                          "KXMLBF5","KXMLBF5SPREAD","KXMLBF5TOTAL",
                          "KXMLBHIT","KXMLBHR","KXMLBHRR","KXMLBKS","KXMLBTB"]),
        ("MLB Season",   ["KXMLB","KXMLBAL","KXMLBNL",
                          "KXMLBALEAST","KXMLBALWEST","KXMLBALCENT",
                          "KXMLBNLEAST","KXMLBNLWEST","KXMLBNLCENT",
                          "KXMLBPLAYOFFS","KXTEAMSINWS",
                          "KXMLBBESTRECORD","KXMLBWORSTRECORD","KXMLBLSTREAK","KXMLBWSTREAK"]),
        ("Team Wins",    ["KXMLBWINS-ATH","KXMLBWINS-ATL","KXMLBWINS-AZ","KXMLBWINS-BAL",
                          "KXMLBWINS-BOS","KXMLBWINS-CHC","KXMLBWINS-CIN","KXMLBWINS-CLE",
                          "KXMLBWINS-COL","KXMLBWINS-CWS","KXMLBWINS-DET","KXMLBWINS-HOU",
                          "KXMLBWINS-KC","KXMLBWINS-LAA","KXMLBWINS-LAD","KXMLBWINS-MIA",
                          "KXMLBWINS-MIL","KXMLBWINS-MIN","KXMLBWINS-NYM","KXMLBWINS-NYY",
                          "KXMLBWINS-PHI","KXMLBWINS-PIT","KXMLBWINS-SD","KXMLBWINS-SEA",
                          "KXMLBWINS-SF","KXMLBWINS-STL","KXMLBWINS-TB","KXMLBWINS-TEX",
                          "KXMLBWINS-TOR","KXMLBWINS-WSH"]),
        ("MLB Awards",   ["KXMLBALMVP","KXMLBNLMVP","KXMLBALCY","KXMLBNLCY",
                          "KXMLBALROTY","KXMLBNLROTY","KXMLBEOTY","KXMLBALMOTY","KXMLBNLMOTY",
                          "KXMLBALHAARON","KXMLBNLHAARON","KXMLBALCPOTY","KXMLBNLCPOTY",
                          "KXMLBALRELOTY","KXMLBNLRELOTY"]),
        ("MLB Stats",    ["KXMLBSTAT","KXMLBSTATCOUNT","KXMLBSEASONHR",
                          "KXLEADERMLBAVG","KXLEADERMLBDOUBLES","KXLEADERMLBERA",
                          "KXLEADERMLBHITS","KXLEADERMLBHR","KXLEADERMLBKS","KXLEADERMLBOPS",
                          "KXLEADERMLBRBI","KXLEADERMLBRUNS","KXLEADERMLBSTEALS",
                          "KXLEADERMLBTRIPLES","KXLEADERMLBWAR","KXLEADERMLBWINS"]),
        ("MLB Other",    ["KXMLBTRADE","KXWSOPENTRANTS"]),
        ("International",["KXNPBGAME","KXKBOGAME","KXNCAABBGAME"]),
        ("NCAA",         ["KXNCAABASEBALL","KXNCAABBGS"]),
    ],
    "Football": [
        ("NFL Games",    ["KXUFLGAME"]),
        ("NFL Season",   ["KXSB","KXNFLPLAYOFF","KXNFLAFCCHAMP","KXNFLNFCCHAMP",
                          "KXNFLAFCEAST","KXNFLAFCWEST","KXNFLAFCNORTH","KXNFLAFCSOUTH",
                          "KXNFLNFCEAST","KXNFLNFCWEST","KXNFLNFCNORTH","KXNFLNFCSOUTH",
                          "KXRECORDNFLBEST","KXRECORDNFLWORST"]),
        ("NFL Awards",   ["KXNFLMVP","KXNFLOPOTY","KXNFLDPOTY","KXNFLOROTY","KXNFLDROTY","KXNFLCOTY"]),
        ("NFL Draft",    ["KXNFLDRAFT1","KXNFLDRAFT1ST","KXNFLDRAFTPICK","KXNFLDRAFTTOP",
                          "KXNFLDRAFTWR","KXNFLDRAFTDB","KXNFLDRAFTTE","KXNFLDRAFTQB",
                          "KXNFLDRAFTOL","KXNFLDRAFTEDGE","KXNFLDRAFTLB","KXNFLDRAFTRB",
                          "KXNFLDRAFTDT","KXNFLDRAFTTEAM"]),
        ("NFL Stats",    ["KXLEADERNFLSACKS","KXLEADERNFLINT","KXLEADERNFLPINT",
                          "KXLEADERNFLPTDS","KXLEADERNFLPYDS","KXLEADERNFLRTDS",
                          "KXLEADERNFLRUSHTDS","KXLEADERNFLRUSHYDS","KXLEADERNFLRYDS",
                          "KXNFLTEAM1POS","KXNFLPRIMETIME"]),
        ("NFL Other",    ["KXNFLTRADE","KXNEXTTEAMNFL","KXKELCERETIRE","KXSTARTINGQBWEEK1",
                          "KXCOACHOUTNFL","KXCOACHOUTNCAAFB","KXARODGRETIRE",
                          "KXRELOCATIONCHI","KX1STHOMEGAME","KXSORONDO","KXDONATEMRBEAST"]),
        ("NCAAF",        ["KXNCAAF","KXHEISMAN","KXNCAAFCONF","KXNCAAFACC","KXNCAAFB10",
                          "KXNCAAFB12","KXNCAAFSEC","KXNCAAFAAC","KXNCAAFSBELT","KXNCAAFMWC",
                          "KXNCAAFMAC","KXNCAAFCUSA","KXNCAAFPAC12","KXNCAAFPLAYOFF",
                          "KXNCAAFFINALIST","KXNCAAFUNDEFEATED","KXNCAAFCOTY","KXNCAAFAPRANK"]),
        ("Other",        ["KXNDJOINCONF","KXCOVEREA"]),
    ],
    "Hockey": [
        ("NHL Games",    ["KXNHLGAME","KXNHLSPREAD","KXNHLTOTAL"]),
        ("NHL Season",   ["KXNHL","KXNHLPLAYOFF","KXTEAMSINSC","KXNHLPRES",
                          "KXNHLEAST","KXNHLWEST","KXNHLADAMS","KXNHLCENTRAL",
                          "KXNHLATLANTIC","KXNHLMETROPOLITAN","KXNHLPACIFIC"]),
        ("NHL Awards",   ["KXNHLHART","KXNHLNORRIS","KXNHLVEZINA","KXNHLCALDER",
                          "KXNHLROSS","KXNHLRICHARD"]),
        ("AHL",          ["KXAHLGAME"]),
        ("International",["KXKHLGAME","KXSHLGAME","KXLIIGAGAME","KXELHGAME","KXNLGAME","KXDELGAME"]),
        ("Other",        ["KXCANADACUP","KXNCAAHOCKEY","KXNCAAHOCKEYGAME"]),
    ],
    "Tennis": [
        ("ATP Matches",  ["KXATPMATCH","KXATPSETWINNER","KXATPCHALLENGERMATCH","KXMCMMEN","KXFOMEN"]),
        ("WTA Matches",  ["KXWTAMATCH","KXFOWOMEN"]),
        ("Grand Slams",  ["KXGRANDSLAM","KXATPGRANDSLAM","KXWTAGRANDSLAM",
                          "KXATPGRANDSLAMFIELD","KXGRANDSLAMJFONSECA"]),
        ("Rankings",     ["KXATP1RANK"]),
        ("Other",        ["KXWTASERENA","KXGOLFTENNISMAJORS"]),
    ],
    "Golf": [
        ("The Masters",  ["KXPGATOUR","KXPGAH2H","KXPGA3BALL","KXPGA5BALL",
                          "KXPGAR1LEAD","KXPGAR1TOP5","KXPGAR1TOP10","KXPGAR1TOP20",
                          "KXPGAR2LEAD","KXPGAR2TOP5","KXPGAR2TOP10",
                          "KXPGAR3LEAD","KXPGAR3TOP5","KXPGAR3TOP10",
                          "KXPGATOP5","KXPGATOP10","KXPGATOP20","KXPGATOP40",
                          "KXPGAPLAYOFF","KXPGACUTLINE","KXPGAMAKECUT","KXPGAAGECUT",
                          "KXPGAWINNERREGION","KXPGALOWSCORE","KXPGASTROKEMARGIN","KXPGAWINNINGSCORE",
                          "KXPGAPLAYERCAT","KXPGABIRDIES","KXPGAROUNDSCORE",
                          "KXPGAEAGLE","KXPGAHOLEINONE","KXPGABOGEYFREE","KXPGAMASTERS"]),
        ("Majors",       ["KXPGAMAJORTOP10","KXPGAMAJORWIN","KXGOLFMAJORS"]),
        ("Ryder Cup",    ["KXPGARYDER","KXPGASOLHEIM","KXRYDERCUPCAPTAIN"]),
        ("Player Props", ["KXPGACURRY","KXPGATIGER","KXBRYSONCOURSERECORDS","KXSCOTTIESLAM",
                          "KXGOLFTENNISMAJORS"]),
    ],
    "MMA": [
        ("UFC Fights",   ["KXUFCFIGHT"]),
        ("UFC Titles",   ["KXUFCHEAVYWEIGHTTITLE","KXUFCLHEAVYWEIGHTTITLE","KXUFCMIDDLEWEIGHTTITLE",
                          "KXUFCWELTERWEIGHTTITLE","KXUFCLIGHTWEIGHTTITLE","KXUFCFEATHERWEIGHTTITLE",
                          "KXUFCBANTAMWEIGHTTITLE","KXUFCFLYWEIGHTTITLE"]),
        ("UFC Other",    ["KXMCGREGORFIGHTNEXT","KXCARDPRESENCEUFCWH","KXUFCWHITEHOUSE"]),
    ],
    "Cricket": [
        ("IPL",          ["KXIPLGAME","KXIPL","KXIPLFOUR","KXIPLSIX","KXIPLTEAMTOTAL"]),
        ("PSL",          ["KXPSLGAME","KXPSL"]),
        ("Other",        ["KXT20MATCH"]),
    ],
    "Esports": [
        ("Valorant",     ["KXVALORANTMAP","KXVALORANTGAME"]),
        ("League of Legends",["KXLOLGAME","KXLOLMAP","KXLOLTOTALMAPS"]),
        ("CS2",          ["KXCS2GAME","KXCS2MAP","KXCS2TOTALMAPS"]),
        ("Rainbow Six",  ["KXR6GAME"]),
        ("Dota 2",       ["KXDOTA2GAME","KXDOTA2MAP"]),
        ("Overwatch",    ["KXOWGAME"]),
    ],
    "Motorsport": [
        ("F1",           ["KXF1RACE","KXF1RACEPODIUM","KXF1TOP5","KXF1TOP10","KXF1FASTLAP",
                          "KXF1CONSTRUCTORS","KXF1RETIRE","KXF1","KXF1OCCUR","KXF1CHINA"]),
        ("NASCAR",       ["KXNASCARCUPSERIES","KXNASCARRACE","KXNASCARTOP3","KXNASCARTOP5",
                          "KXNASCARTOP10","KXNASCARTOP20","KXNASCARTRUCKSERIES","KXNASCARAUTOPARTSSERIES"]),
        ("MotoGP",       ["KXMOTOGP","KXMOTOGPTEAMS"]),
        ("IndyCar",      ["KXINDYCARSERIES"]),
    ],
    "Boxing": [
        ("Fights",       ["KXBOXING","KXFLOYDTYSONFIGHT"]),
        ("WBC Titles",   ["KXWBCHEAVYWEIGHTTITLE","KXWBCCRUISERWEIGHTTITLE","KXWBCMIDDLEWEIGHTTITLE",
                          "KXWBCWELTERWEIGHTTITLE","KXWBCLIGHTWEIGHTTITLE","KXWBCFEATHERWEIGHTTITLE",
                          "KXWBCBANTAMWEIGHTTITLE","KXWBCFLYWEIGHTTITLE"]),
    ],
    "Rugby": [
        ("NRL",          ["KXRUGBYNRLMATCH","KXNRLCHAMP"]),
        ("Premiership",  ["KXPREMCHAMP"]),
        ("Super League", ["KXSLRCHAMP"]),
        ("Top 14",       ["KXFRA14CHAMP"]),
    ],
    "Lacrosse": [
        ("NCAA",         ["KXNCAAMLAXGAME","KXNCAALAXFINAL"]),
        ("Awards",       ["KXLAXTEWAARATON"]),
    ],
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def safe_date(val):
    try:
        if val is None or val == "": return None
        ts = pd.to_datetime(val, utc=True)
        if pd.isna(ts): return None
        return ts.to_pydatetime().astimezone(UTC).date()
    except: return None

def safe_dt(val):
    """Return full datetime (timezone-aware) or None."""
    try:
        if val is None or val == "": return None
        if isinstance(val, str) and val.strip() in ("", "NaT", "None", "nan"): return None
        ts = pd.to_datetime(val, utc=True)
        if pd.isna(ts): return None
        return ts.to_pydatetime().astimezone(UTC)
    except: return None

def parse_game_date_from_ticker(event_ticker: str):
    """Extract game date from Kalshi event ticker.
    e.g. KXEPLGAME-26APR25ARSNEW  -> date(2026, 4, 25)
         KXCONMEBOLLIBGAME-26APR09UCVLIB -> date(2026, 4, 9)
    Pattern after first '-': YYMONDD (e.g. 26APR25)
    """
    import re
    from datetime import date as _date
    MONTHS = {"JAN":1,"FEB":2,"MAR":3,"APR":4,"MAY":5,"JUN":6,
              "JUL":7,"AUG":8,"SEP":9,"OCT":10,"NOV":11,"DEC":12}
    try:
        # Get the part after the series- prefix, e.g. "26APR25ARSNEW"
        parts = event_ticker.split("-")
        if len(parts) < 2: return None
        seg = parts[1]  # e.g. "26APR25ARSNEW"
        m = re.match(r"(\d{2})([A-Z]{3})(\d{2})", seg)
        if not m: return None
        yy, mon, dd = m.group(1), m.group(2), m.group(3)
        yr = 2000 + int(yy)
        mo = MONTHS.get(mon)
        if not mo: return None
        return _date(yr, mo, int(dd))
    except: return None

def get_game_datetime_from_sub_title(sub_title: str):
    """Parse sub_title like 'ARS vs NEW (Apr 25)' -> month/day hint."""
    import re
    try:
        m = re.search(r"\(([A-Za-z]+)\s+(\d+)\)", sub_title)
        if m:
            return m.group(1), int(m.group(2))
    except: pass
    return None, None

def fmt_date(d):
    from datetime import datetime, date as _date
    try:
        if d is None: return ""
        if hasattr(d, 'hour'):
            try:
                import pytz
                eastern = pytz.timezone('US/Eastern')
            except ImportError:
                from zoneinfo import ZoneInfo
                eastern = ZoneInfo('America/New_York')
            if d.tzinfo:
                d = d.astimezone(eastern)
            tz_label = d.strftime('%Z') or "ET"
            hour = d.hour % 12 or 12
            ampm = "am" if d.hour < 12 else "pm"
            return f"{d.strftime('%b')} {d.day}, {hour}:{d.strftime('%M')}{ampm} {tz_label}"
        return d.strftime("%b %d")
    except:
        try: return d.strftime("%b %d") if d else ""
        except: return ""


def fmt_pct(v):
    try:
        f = float(v)
        return f"{int(round(f*100)) if f<=1.0 else int(round(f))}%"
    except: return "—"

# ── API ───────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_client():
    from kalshi_python_sync import Configuration, KalshiClient
    key_id  = st.secrets["KALSHI_API_KEY_ID"]
    key_str = st.secrets["KALSHI_PRIVATE_KEY"]
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".pem") as f:
        f.write(key_str); pem = f.name
    cfg = Configuration()
    cfg.api_key_id = key_id
    cfg.private_key_pem_path = pem
    return KalshiClient(cfg)

client = get_client()

def paginate(with_markets=False, category=None, max_pages=30):
    events, cursor = [], None
    for _ in range(max_pages):
        try:
            kw = {"limit":200,"status":"open"}
            if with_markets: kw["with_nested_markets"] = True
            if category:     kw["category"] = category
            if cursor:       kw["cursor"] = cursor
            resp  = client.get_events(**kw).to_dict()
            batch = resp.get("events",[])
            if not batch: break
            events.extend(batch)
            cursor = resp.get("cursor") or resp.get("next_cursor")
            if not cursor: break
            time.sleep(0.05)
        except Exception as e:
            if "429" in str(e): time.sleep(3)
            else: break
    return events

@st.cache_data(ttl=1800)
def fetch_all():
    prog = st.progress(0, text="Loading markets…")

    all_ev = paginate(with_markets=True, max_pages=30)
    prog.progress(0.80, text=f"{len(all_ev)} events loaded…")
    combined = all_ev
    if not combined:
        prog.empty(); return pd.DataFrame()

    df = pd.DataFrame(combined)
    df["category"] = df.get("category", pd.Series("Other", index=df.index)).fillna("Other").str.strip()
    df["_series"]  = df.get("series_ticker", pd.Series("", index=df.index)).fillna("").str.upper()
    df["_sport"]   = df["_series"].apply(get_sport)
    df["_is_sport"]= df["_sport"] != ""

    # Ensure markets column exists and is always a list
    if "markets" not in df.columns:
        df["markets"] = [[] for _ in range(len(df))]
    df["markets"] = df["markets"].apply(lambda x: x if isinstance(x, list) else [])
    df["_soccer_comp"] = df.apply(
        lambda r: SOCCER_COMP.get(r["_series"],"Other") if r["_sport"]=="Soccer" else "", axis=1
    )

    if "markets" not in df.columns:
        df["markets"] = [[] for _ in range(len(df))]
    else:
        df["markets"] = df["markets"].apply(lambda x: x if isinstance(x,list) else [])

    def extract(row):
        mkts = row.get("markets")
        if not isinstance(mkts, list) or not mkts:
            return "—", "—", None, None, None, None, []

        first_mk   = mkts[0]
        event_ticker = str(row.get("event_ticker", ""))
        sport        = str(row.get("_sport", ""))

        # ── Game date from ticker (most reliable) ──
        game_date = parse_game_date_from_ticker(event_ticker)

        # ── Collect all time fields from market ──
        open_dt              = safe_dt(first_mk.get("open_time"))
        close_dt             = safe_dt(first_mk.get("close_time"))
        exp_dt               = safe_dt(first_mk.get("expected_expiration_time"))

        # ── Estimate kickoff time ──
        # For game events, expected_expiration_time is set to ~game end
        # Subtract sport-specific duration to get kickoff estimate
        # Soccer: 90min + stoppage ≈ 105min → subtract 2h from exp_dt
        # Baseball: ~3h → subtract 3h
        # Basketball/Hockey: ~2.5h → subtract 2.5h
        # Football: ~3h → subtract 3h
        # Default: subtract 2h
        from datetime import timedelta as _td
        DURATION = {
            "Soccer": _td(hours=2), "Baseball": _td(hours=3),
            "Basketball": _td(hours=2, minutes=30),
            "Hockey": _td(hours=2, minutes=30),
            "Football": _td(hours=3),
            "Cricket": _td(hours=4),
        }
        duration = DURATION.get(sport, _td(hours=2))
        kickoff_dt = None
        if game_date and exp_dt:
            # Use exp_dt - duration as kickoff estimate
            kickoff_dt = exp_dt - duration
        elif game_date and close_dt:
            kickoff_dt = close_dt - duration

        # ── sort date ──
        sort_dt = game_date if game_date else (close_dt.date() if close_dt else None)

        # ── Begins / Live status ──
        from datetime import date as _date, datetime as _dt
        today = _date.today()
        now   = _dt.now(UTC)

        # No begins text — date shown via display_dt
        begins = ""

        # ── Outcome labels from yes_sub_title ──
        outcomes = []
        for mk in mkts:
            label = str(mk.get("yes_sub_title") or "").strip()
            if not label:
                t = str(mk.get("ticker") or "")
                parts = t.rsplit("-", 1)
                label = parts[-1] if len(parts) > 1 else t

            yf = nf = None
            try:
                yd = mk.get("yes_bid_dollars")
                nd = mk.get("no_bid_dollars")
                if yd is not None: yf = float(yd)
                if nd is not None: nf = float(nd)
                if yf is None:
                    yb = mk.get("yes_bid")
                    if yb is not None: yf = float(yb) / 100
                if nf is None:
                    nb = mk.get("no_bid")
                    if nb is not None: nf = float(nb) / 100
            except: pass

            chance = f"{int(round(yf*100))}%" if yf is not None else "—"
            yes    = f"{int(round(yf*100))}¢"  if yf is not None else "—"
            no     = f"{int(round(nf*100))}¢"  if nf is not None else "—"
            outcomes.append((label[:35], chance, yes, no))

        return "—", "—", sort_dt, game_date, kickoff_dt, begins, outcomes
    info = df.apply(extract, axis=1, result_type="expand")
    df["_yes"] = info[0]; df["_no"] = info[1]; df["_mkt_dt"] = info[2]; df["_game_date"] = info[3]; df["_kickoff_dt"] = info[4]; df["_begins"] = info[5]; df["_outcomes"] = info[6]



    df["_sort_dt"] = df["_mkt_dt"]  # sort_dt is already set in extract
    def get_display_dt(row):
        # Only show date/time for events that have a kickoff estimate
        kdt = row.get("_kickoff_dt")
        if kdt: return fmt_date(kdt)
        return ""
    df["_display_dt"] = df.apply(get_display_dt, axis=1)

    # "Begins in" — use open_time or start_date from event or first market
    # _begins already computed in extract()

    prog.progress(1.0); prog.empty()
    return df

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📡 Kalshi Terminal")

    today = date.today()
    date_mode = st.radio("📅 Date", ["All dates","Today","This week","Custom"], index=0)
    d_start = d_end = None
    if date_mode == "Today":     d_start = d_end = today
    elif date_mode == "This week": d_start, d_end = today, today+timedelta(days=6)
    elif date_mode == "Custom":
        d_start = st.date_input("From", value=today)
        d_end   = st.date_input("To",   value=today+timedelta(days=7))
    include_no_date = st.checkbox("Include undated events", value=True)
    st.markdown("---")
    st.caption("Cached 30 min.")

# ── Load & filter ─────────────────────────────────────────────────────────────
st.title("📡 Kalshi Markets Terminal")

# ── Top controls bar ─────────────────────────────────────────────────────────
_c1, _c2, _c3 = st.columns([3, 1.2, 1.2])
with _c1:
    search = st.text_input("", placeholder="🔍  Search team, player, market…",
                           label_visibility="collapsed")
with _c2:
    sort_by = st.selectbox("Sort", ["Earliest first","Latest first","Default"],
                           index=0, label_visibility="collapsed")
with _c3:
    st.markdown("<div style='padding-top:4px'></div>", unsafe_allow_html=True)
    if st.button("🔄 Refresh data", use_container_width=True):
        fetch_all.clear(); st.rerun()
with st.spinner("Loading…"):
    df = fetch_all()

if df.empty:
    st.error("No data. Check API credentials."); st.stop()

filtered = df.copy()
if date_mode != "All dates":
    def date_ok(row):
        if row["_is_sport"]: return True
        d = row["_sort_dt"]
        if d is None: return include_no_date
        try: return d_start <= d <= d_end
        except: return include_no_date
    filtered = filtered[filtered.apply(date_ok, axis=1)]

if search:
    s = search.lower()
    mask = (filtered["title"].str.lower().str.contains(s, na=False) |
            filtered["event_ticker"].str.lower().str.contains(s, na=False) |
            filtered["category"].str.lower().str.contains(s, na=False))
    filtered = filtered[mask]

if sort_by != "Default":
    asc = sort_by == "Earliest first"
    from datetime import date as _sortdate
    def _sort_key(d):
        if d is None: return "9999-99-99"
        if isinstance(d, _sortdate): return d.isoformat()
        try: return str(d)
        except: return "9999-99-99"
    filtered = filtered.copy()
    filtered["_sk"] = filtered["_sort_dt"].apply(_sort_key)
    # Put nulls at end regardless of direction
    has_date = filtered["_sk"] != "9999-99-99"
    dated   = filtered[has_date].sort_values("_sk", ascending=asc)
    undated = filtered[~has_date]
    filtered = pd.concat([dated, undated], ignore_index=True)
    filtered = filtered.drop(columns=["_sk"])

sport_count = int(df["_is_sport"].sum())
st.markdown(f"""<div class="metric-strip">
  <div class="metric-box"><div class="metric-label">Total markets</div><div class="metric-value">{len(df)}</div></div>
  <div class="metric-box"><div class="metric-label">Sports</div><div class="metric-value">{sport_count}</div></div>
  <div class="metric-box"><div class="metric-label">Showing</div><div class="metric-value">{len(filtered)}</div></div>
</div>""", unsafe_allow_html=True)



# ── Render ────────────────────────────────────────────────────────────────────
def render_cards(data):
    if data.empty:
        st.markdown('<div class="empty-state">No markets found.</div>', unsafe_allow_html=True)
        return
    html = '<div class="card-grid">'
    for _, row in data.iterrows():
        try:
            ticker  = str(row.get("event_ticker","")).upper()
            cat     = str(row.get("category","Other"))
            title   = str(row.get("title",""))[:90]
            sport   = str(row.get("_sport",""))
            base_ic, pill = CAT_META.get(cat, ("📊","pill-default"))
            icon    = SPORT_ICONS.get(sport, base_ic) if sport else base_ic
            label   = sport[:16] if sport else cat[:16]
            dt      = str(row.get("_display_dt","Open"))
            begins  = str(row.get("_begins") or "")
            yes     = str(row.get("_yes","—"))
            no      = str(row.get("_no","—"))
            outcomes = row.get("_outcomes") or []
            # Build URL: https://kalshi.com/markets/{series_lower}/slug/{ticker_lower}
            series_lower = str(row.get("series_ticker","")).lower()
            ticker_lower = ticker.lower()
            kalshi_url = f"https://kalshi.com/markets/{series_lower}/{series_lower.replace('kx','')}/{ticker_lower}" if series_lower else ""
            link_html = f'<a class="ticker-link" href="{kalshi_url}" target="_blank">{ticker}</a>' if kalshi_url else f'<span class="ticker-text">{ticker}</span>'
            # Build outcomes rows
            if outcomes:
                odds_html = ""
                for (olabel, ochance, oyes, ono) in outcomes[:5]:
                    safe_label = olabel[:30] if olabel else "—"
                    odds_html += f'''<div class="outcome-row">
<div class="outcome-label">{safe_label}</div>
<div class="outcome-chance">{ochance}</div>
<div class="outcome-odds">
<div class="odds-yes"><div class="odds-label">YES</div><div class="odds-price-yes">{oyes}</div></div>
<div class="odds-no"><div class="odds-label">NO</div><div class="odds-price-no">{ono}</div></div>
</div></div>'''
            else:
                odds_html = '<div class="outcome-row"><div class="outcome-label">—</div><div class="outcome-chance">—</div><div class="outcome-odds"><div class="odds-yes"><div class="odds-label">YES</div><div class="odds-price-yes">—</div></div><div class="odds-no"><div class="odds-label">NO</div><div class="odds-price-no">—</div></div></div></div>'
            is_live_card = "Live" in begins
            dt_html = '<div class="card-timing"><span class="date-text">' + dt + '</span></div>' if dt else ''
            html += (
                '<div class="market-card">'
                '<div class="card-top"><span class="cat-pill ' + pill + '">' + label + '</span></div>'
                + dt_html +
                '<span class="card-icon">' + icon + '</span>'
                '<div class="card-title">' + title + '</div>'
                '<div class="card-footer">' + link_html + odds_html + '</div>'
                '</div>'
            )
        except: continue
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

# Build series-to-subtab lookup
SERIES_TO_SUBTAB = {}  # sport → {series → tab_name}
for sport, tabs in SPORT_SUBTABS.items():
    SERIES_TO_SUBTAB[sport] = {}
    for tab_name, series_list in tabs:
        for s in series_list:
            SERIES_TO_SUBTAB[sport][s] = tab_name

def render_subtabs(sport_df, sport):
    tabs_def = SPORT_SUBTABS.get(sport)
    if not tabs_def:
        render_cards(sport_df); return

    # Map each row to its subtab using series ticker
    sport_df = sport_df.copy()
    lookup = SERIES_TO_SUBTAB.get(sport, {})
    sport_df["_subtab"] = sport_df["_series"].apply(lambda s: lookup.get(s, "Other"))

    # Only show tabs that have data
    present = []
    for tab_name, _ in tabs_def:
        if (sport_df["_subtab"] == tab_name).any():
            present.append(tab_name)
    # Add Other if there are uncategorized items
    other_df = sport_df[~sport_df["_subtab"].isin([t for t,_ in tabs_def])]
    has_other = not other_df.empty

    if not present and not has_other:
        render_cards(sport_df); return

    tab_labels = ["All"] + present + (["Other"] if has_other else [])
    tabs = st.tabs(tab_labels)
    with tabs[0]: render_cards(sport_df)
    for i, tab_name in enumerate(present):
        with tabs[i+1]:
            render_cards(sport_df[sport_df["_subtab"]==tab_name])
    if has_other:
        with tabs[-1]: render_cards(other_df)

def render_soccer(sdf):
    comps = sorted([c for c in sdf["_soccer_comp"].unique() if c and c != "Other"])
    has_other = (sdf["_soccer_comp"] == "Other").any() or (sdf["_soccer_comp"] == "").any()
    if not comps:
        render_cards(sdf); return
    tabs = st.tabs(["All"] + comps + (["Other"] if has_other else []))
    with tabs[0]: render_cards(sdf)
    for i, comp in enumerate(comps):
        with tabs[i+1]: render_cards(sdf[sdf["_soccer_comp"]==comp])
    if has_other:
        with tabs[-1]: render_cards(sdf[sdf["_soccer_comp"].isin(["Other",""])])

def render_sports(sdf):
    sports_present = [s for s in _SPORT_SERIES.keys() if s in sdf["_sport"].values]
    if not sports_present:
        render_cards(sdf); return
    labels = ["🏟️ All"] + [f"{SPORT_ICONS.get(s,'🏆')} {s}" for s in sports_present]
    tabs = st.tabs(labels)
    with tabs[0]: render_cards(sdf)
    for i, sport in enumerate(sports_present):
        with tabs[i+1]:
            sport_df = sdf[sdf["_sport"]==sport].copy()
            if sport == "Soccer":
                render_soccer(sport_df)
            else:
                render_subtabs(sport_df, sport)

def render_cat_tabs(cat_df, cat):
    tags = CAT_TAGS.get(cat, [])
    if not tags:
        render_cards(cat_df); return
    ttabs = st.tabs(["All"] + tags)
    with ttabs[0]: render_cards(cat_df)
    for i, tag in enumerate(tags):
        with ttabs[i+1]:
            render_cards(cat_df[cat_df["title"].str.contains(tag, case=False, na=False)])

# ── Main tabs ─────────────────────────────────────────────────────────────────
present_cats = ["All"] + [c for c in TOP_CATS
    if (c=="Sports" and sport_count>0) or (c!="Sports" and c in df["category"].values)]
top_tabs = st.tabs(present_cats)
for i, tab in enumerate(top_tabs):
    with tab:
        cat = present_cats[i]
        if cat == "All":      render_cards(filtered)
        elif cat == "Sports": render_sports(filtered[filtered["_is_sport"]].copy())
        else:                 render_cat_tabs(filtered[filtered["category"]==cat].copy(), cat)


st.markdown("<hr><p style='text-align:center;color:#1f2937;font-size:11px;'>KALSHI TERMINAL · CACHED 30 MIN · NOT FINANCIAL ADVICE</p>", unsafe_allow_html=True)
