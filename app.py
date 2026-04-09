import streamlit as st
import pandas as pd
import tempfile
import time
from datetime import date, timedelta, timezone

st.set_page_config(page_title="Kalshi Terminal", layout="wide", page_icon="📡")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@700;800&display=swap');
html,body,[class*="css"]{font-family:'DM Mono',monospace;}
.stApp{background:#0a0a0f;}
section[data-testid="stSidebar"]{background:#0f0f1a!important;border-right:1px solid #1e1e32;}
section[data-testid="stSidebar"] label,section[data-testid="stSidebar"] p{color:#6b7280!important;font-size:11px!important;letter-spacing:.08em;text-transform:uppercase;}
h1{font-family:'Syne',sans-serif!important;font-weight:800!important;color:#f0f0ff!important;letter-spacing:-.02em;font-size:2.2rem!important;}
.metric-strip{display:flex;gap:12px;margin-bottom:28px;flex-wrap:wrap;}
.metric-box{background:#0f0f1a;border:1px solid #1e1e32;border-radius:10px;padding:14px 20px;flex:1;min-width:120px;}
.metric-label{font-size:10px;color:#4b5563;text-transform:uppercase;letter-spacing:.1em;margin-bottom:4px;}
.metric-value{font-size:22px;font-weight:500;color:#a5b4fc;}
.card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px;}
.market-card{background:#0f0f1a;border:1px solid #1e1e32;border-radius:12px;padding:18px 20px;transition:border-color .2s,transform .15s;position:relative;}
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
.date-text{font-size:11px;color:#6b7280;}
.card-icon{font-size:20px;margin-bottom:6px;display:block;}
.card-title{font-size:14px;font-weight:500;color:#e2e8f0;line-height:1.45;margin-bottom:12px;min-height:58px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;}
.card-footer{border-top:1px solid #1a1a2e;padding-top:10px;}
.ticker-text{font-size:10px;color:#374151;letter-spacing:.06em;display:block;margin-bottom:8px;}
.odds-row{display:flex;gap:8px;}
.odds-yes{flex:1;background:#0d2d1a;border:1px solid #166534;border-radius:6px;padding:5px 8px;text-align:center;}
.odds-no{flex:1;background:#2d0d0d;border:1px solid #7f1d1d;border-radius:6px;padding:5px 8px;text-align:center;}
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
    "Elections":["US Elections","International elections","House","Primaries"],
    "Politics":["Trump","Congress","International","SCOTUS & courts","Local","Iran"],
    "Economics":["Fed","Inflation","GDP","Jobs & Economy","Housing","Oil and energy","Global Central Banks"],
    "Financials":["S&P","Nasdaq","Metals","Agriculture","Oil & Gas","Treasuries","EUR/USD","USD/JPY"],
    "Crypto":["BTC","ETH","SOL","DOGE","XRP","BNB","HYPE"],
    "Companies":["IPOs","Elon Musk","CEOs","Product launches","Layoffs"],
    "Entertainment":["Music","Television","Movies","Awards","Video games","Oscars"],
    "Climate and Weather":["Hurricanes","Daily temperature","Snow and rain","Climate change","Natural disasters"],
    "Science and Technology":["AI","Space","Medicine","Energy"],
    "Health":["Diseases"],
    "Mentions":["Earnings","Politicians","Sports"],
}

# Sub-category tags for each sport — used to build drill-down tabs
# Each entry is (tab_label, search_terms_in_title_or_ticker)
SPORT_SUBTAGS = {
    "Basketball": [
        ("NBA",          ["NBA","KXNBA"]),
        ("Playoffs",     ["playoff","playin","KXNBAPLAYOFF","KXNBAPLAYIN"]),
        ("Draft",        ["draft","KXNBADRAFT"]),
        ("Awards",       ["MVP","ROY","COY","DPOY","KXNBAMVP","KXNBAROY","KXNBACOY","KXNBADPOY","KXNBASIXTH","KXNBAMIMP"]),
        ("All-Star",     ["all-star","KXNBA1STTEAM","KXNBA2NDTEAM","KXNBA3RDTEAM"]),
        ("Standings",    ["wins","east","west","atlantic","central","pacific","southeast","southwest","northwest","KXNBAWINS","KXNBAEAST","KXNBAWEST"]),
        ("International",["euroleague","BSL","BBL","ACB","ISL","ABL","CBA","KXEUROLEAGUEGAME","KXBSLGAME","KXBBLGAME","KXACBGAME","KXISLGAME","KXABAGAME","KXCBAGAME"]),
        ("NCAAB",        ["NCAAB","NCAAMB","march madness","KXMARMAD","KXNCAAMB"]),
        ("WNBA",         ["WNBA","KXWNBA"]),
    ],
    "Baseball": [
        ("MLB Games",    ["KXMLBGAME"]),
        ("Standings",    ["wins","east","west","central","KXMLBWINS","KXMLBALEAST","KXMLBALWEST","KXMLBALCENT","KXMLBNLEAST","KXMLBNLWEST","KXMLBNLCENT"]),
        ("Awards",       ["MVP","Cy Young","ROY","KXMLBALMVP","KXMLBNLMVP","KXMLBALCY","KXMLBNLCY","KXMLBALROTY","KXMLBNLROTY","KXMLBEOTY","KXMLBALMOTY","KXMLBNLMOTY"]),
        ("Playoffs",     ["playoff","World Series","KXMLBPLAYOFFS","KXTEAMSINWS"]),
        ("Stats Leaders",["leader","home run","hits","RBI","ERA","KXLEADERMLB"]),
        ("NCAA Baseball",["NCAABASEBALL","KXNCAABASEBALL","KXNCAABBGS"]),
    ],
    "Football": [
        ("NFL Games",    ["KXUFLGAME"]),
        ("Super Bowl",   ["Super Bowl","KXSB"]),
        ("Playoffs",     ["playoff","AFC champ","NFC champ","KXNFLPLAYOFF","KXNFLAFCCHAMP","KXNFLNFCCHAMP"]),
        ("Standings",    ["AFC","NFC","east","west","north","south","KXNFLAFCEAST","KXNFLAFCWEST","KXNFLAFCNORTH","KXNFLAFCSOUTH","KXNFLNFCEAST","KXNFLNFCWEST","KXNFLNFCNORTH","KXNFLNFCSOUTH"]),
        ("Awards",       ["MVP","OPOTY","DPOTY","OROTY","DROTY","COTY","KXNFLMVP","KXNFLOPOTY","KXNFLDPOTY","KXNFLOROTY","KXNFLDROTY","KXNFLCOTY"]),
        ("Draft",        ["draft","KXNFLDRAFT"]),
        ("Stats Leaders",["leader","passing","rushing","receiving","sacks","KXLEADERNFL"]),
        ("NCAAF",        ["NCAAF","Heisman","KXNCAAF","KXHEISMAN"]),
        ("Trades",       ["trade","KXNFLTRADE","KXNEXTTEAMNFL"]),
    ],
    "Hockey": [
        ("NHL Games",    ["KXNHLGAME"]),
        ("Stanley Cup",  ["Stanley Cup","KXTEAMSINSC","KXNHLPLAYOFF"]),
        ("Standings",    ["east","west","atlantic","metropolitan","central","pacific","KXNHLEAST","KXNHLWEST","KXNHLADAMS","KXNHLCENTRAL","KXNHLATLANTIC","KXNHLMETROPOLITAN","KXNHLPACIFIC"]),
        ("Awards",       ["Hart","Norris","Vezina","Calder","Ross","Richard","Pres","KXNHLHART","KXNHLNORRIS","KXNHLVEZINA","KXNHLCALDER","KXNHLROSS","KXNHLRICHARD","KXNHLPRES"]),
        ("Spreads/Totals",["KXNHLSPREAD","KXNHLTOTAL"]),
        ("NCAA Hockey",  ["NCAAHOCKEY","KXNCAAHOCKEY"]),
        ("Canada Cup",   ["Canada Cup","KXCANADACUP"]),
    ],
    "Tennis": [
        ("Grand Slams",  ["Grand Slam","KXGRANDSLAM","KXATPGRANDSLAM","KXWTAGRANDSLAM","KXATPGRANDSLAMFIELD",
                          "KXTENNISGRANDSLAM","French Open","Wimbledon","US Open","Australian Open",
                          "KXFOPENMENSINGLE","KXFOPENWMENSINGLE","KXAOMENSINGLES","KXAOWOMEN",
                          "KXUSOMENSINGLES","KXUSOWOMENSINGLES","KXWMENSINGLES","KXWWOMENSINGLES",
                          "KXFOMENSINGLES","KXFOWOMENSINGLES"]),
        ("Monte Carlo",  ["Monte Carlo","KXATPMC","KXMCMMEN","KXMCMEN","monte-carlo"]),
        ("ATP Matches",  ["KXATPGAME","KXATPMATCH","KXATPSETWINNER","KXATPANYSET","KXATPEXACTMATCH",
                          "KXATPGAMESPREAD","KXATPGAMETOTAL","KXATPGSPREAD","KXATPDOUBLES",
                          "KXATPCHALLENGERMATCH","KXCHALLENGERMATCH","KXATPMAD","KXATPMIA",
                          "KXATPIWO","KXATPAMT","KXATPIT","KXATPWDDF","KXATPMCO",
                          "KXROMENSSINGLES","KXROMENSDOUBLES","KXIWMEN","KXIWMENDOUBLES",
                          "KXMOMEN","KXDDFMENSINGLES","KXQEMOMENSSINGLES","KXO13MENSINGLES",
                          "KXFOMEN"]),
        ("WTA Matches",  ["KXWTAGAME","KXWTAMATCH","KXWTADOUBLES","KXWTACHALLENGERMATCH",
                          "KXWTAMAD","KXWTAMIA","KXWTAIWO","KXWTAATX","KXWTAMOA","KXWTAIT",
                          "KXWTADDF","KXWTASERENA","KXFOWOMEN","KXIWWOMEN","KXMOWOMEN",
                          "KXDDFWOMENSINGLES","KXUSOWOMENSINGLES","KXQOWOMENSINGLES","KXFOWOMENSINGLES"]),
        ("ATP Futures",  ["KXATPFINALS","KXATPNEXTGEN","KXATPRANK","KXATP1RANK",
                          "KXATPGRANDSLAM","KXATPGRANDSLAMFIELD","KXGRANDSLAM","KXGRANDSLAMJFONSECA",
                          "KXTENNISMAJORDJOKOVIC","KXALCARAZCOACH"]),
        ("WTA Futures",  ["KXWTAFINALS","KXWTAGRANDSLAM"]),
        ("Team Events",  ["Davis Cup","Laver Cup","United Cup","Six Kings","KXDAVISCUP",
                          "KXLAVERCUP","KXUNITEDCUP","KXSIXKINGSSLAM","KXBATTLEOFSEXES"]),
        ("Golf+Tennis",  ["KXGOLFTENNISMAJORS"]),
    ],
    "Golf": [
        ("PGA Tour",     ["PGA","KXPGATOUR","KXPGAH2H","KXPGAMASTERS"]),
        ("Majors",       ["major","Masters","KXGOLFMAJORS","KXPGAMAJOR"]),
        ("Round Leaders",["KXPGAR1LEAD","KXPGAR2LEAD","KXPGAR3LEAD","KXPGAR3TOP"]),
        ("Top Finishes", ["KXPGATOP","KXPGAPLAYOFF","KXPGACUTLINE","KXPGAWINNERREGION","KXPGALOWSCORE"]),
        ("Prop Bets",    ["eagle","hole in one","bogey","5 ball","KXPGAEAGLE","KXPGAHOLEINONE","KXPGABOGEYFREE","KXPGA5BALL"]),
        ("Ryder Cup",    ["Ryder","Solheim","KXPGARYDER","KXPGASOLHEIM","KXRYDERCUPCAPTAIN"]),
        ("Player Props", ["Curry","Tiger","Bryson","KXPGACURRY","KXPGATIGER","KXBRYSONCOURSERECORDS","KXSCOTTIESLAM"]),
    ],
    "MMA": [
        ("UFC Fights",   ["KXUFCFIGHT"]),
        ("Heavyweight",  ["heavyweight","KXUFCHEAVYWEIGHT"]),
        ("Light Heavy",  ["light heavy","KXUFCLHEAVY"]),
        ("Middleweight", ["middleweight","KXUFCMIDDLEWEIGHT"]),
        ("Welterweight", ["welterweight","KXUFCWELTERWEIGHT"]),
        ("Lightweight",  ["lightweight","KXUFCLIGHTWEIGHT"]),
        ("Featherweight",["featherweight","KXUFCFEATHERWEIGHT"]),
        ("Bantamweight", ["bantamweight","KXUFCBANTAMWEIGHT"]),
        ("Flyweight",    ["flyweight","KXUFCFLYWEIGHT"]),
        ("McGregor",     ["McGregor","KXMCGREGOR"]),
    ],
    "Motorsport": [
        ("F1",           ["F1","Formula","KXKF1","KXF1"]),
        ("NASCAR Cup",   ["NASCAR","cup series","KXNASCARCUPSERIES","KXNASCARRACE"]),
        ("NASCAR Other", ["truck","auto parts","KXNASCARTRUCKSERIES","KXNASCARAUTOPARTSSERIES"]),
        ("NASCAR Finish",["KXNASCARTOP"]),
        ("MotoGP",       ["MotoGP","KXMOTOGP"]),
        ("IndyCar",      ["IndyCar","KXINDYCARSERIES"]),
    ],
    "Cricket": [
        ("IPL",          ["IPL","KXIPL","KXIPLGAME"]),
        ("PSL",          ["PSL","KXPSL","KXPSLGAME"]),
    ],
    "Esports": [
        ("Valorant",     ["Valorant","KXVALORANT"]),
        ("League of Legends",["LOL","league of legends","KXLOL"]),
        ("Rainbow Six",  ["R6","Rainbow","KXR6"]),
    ],
    "Boxing": [
        ("Heavyweight",  ["heavyweight","KXWBCHEAVY"]),
        ("Cruiserweight",["cruiserweight","KXWBCCRUISER"]),
        ("Light Heavy",  ["light heavy"]),
        ("Middleweight", ["middleweight","KXWBCMIDDLE"]),
        ("Welterweight", ["welterweight","KXWBCWELTER"]),
        ("Lightweight",  ["lightweight","KXWBCLIGHT"]),
        ("Featherweight",["featherweight","KXWBCFEATHER"]),
        ("Bantamweight", ["bantamweight","KXWBCBANTAM"]),
        ("Flyweight",    ["flyweight","KXWBCFLY"]),
        ("Floyd/Tyson",  ["Floyd","Tyson","KXFLOYDTYSON"]),
    ],
    "Rugby": [
        ("NRL",          ["NRL","KXNRL"]),
        ("Premiership",  ["Premiership","KXPREMCHAMP"]),
        ("French Top 14",["Top 14","Ligue","KXFRA14"]),
        ("Super League", ["Super League","KXSLR"]),
    ],
    "Lacrosse": [
        ("NCAA",         ["NCAA","KXNCAAMLAX","KXNCAALAX"]),
        ("Awards",       ["Tewaaraton","KXLAXTEWAARATON"]),
    ],
}

SPORT_TAGS = [
    ("⚽","Soccer",["KXDFBPOKAL","KXARGPREMDIVGAME","KXLIGUE1SPREAD","KXUSL","KXUELSPREAD","KXEKSTRAKLASA","KXSERIEATOTAL","KXLALIGATOTAL","KXEPLTOP4","KXLALIGABTTS","KXEPLGAME","KXWCGROUPWIN","KXJOINLEAGUE","KXCHNSL","KXWCGAME","KXDIMAYORGAME","KXAPFDDHGAME","KXWCGOALLEADER","KXBUNDESLIGATOTAL","KXEPLTOTAL","KXSCOTTISHPREMGAME","KXSERIEA1H","KXEPLSPREAD","KXCHLLDPGAME","KXECULP","KXSOCCERPLAYMESSI","KXLEADERUCLGOALS","KXURYPD","KXLIGUE11H","KXBUNDESLIGA2GAME","KXLIGUE1BTTS","KXEFLPROMO","KXUSLGAME","KXKLEAGUE","KXUCLW","KXJOINRONALDO","KXSAUDIPLSPREAD","KXTHAIL1","KXMLSBTTS","KXBELGIANPL","KXEPL1H","KXLAMINEYAMAL","KXBALLONDOR","KXSOCCERTRANSFER","KXSAUDIPLTOTAL","KXWCSQUAD","KXSERIEAGAME","KXSERIEARELEGATION","KXKLEAGUEGAME","KXLIGAMXTOTAL","KXEPLTOP6","KXSUPERLIG","KXARSENALCUPS","KXUCLGAME","KXVENFUTVE","KXSERIEBGAME","KXEGYPLGAME","KXALEAGUETOTAL","KXLIGUE1RELEGATION","KXEPLBTTS","KXFACUP","KXMENWORLDCUP","KXSERIEASPREAD","KXFIFAUSPULL","KXUCL1H","KXLALIGARELEGATION","KXLIGAPORTUGALGAME","KXCOPPAITALIA","KXTHAIL1GAME","KXALEAGUESPREAD","KXSAUDIPLGAME","KXPREMIERLEAGUE","KXLIGAMX","KXLALIGASPREAD","KXDENSUPERLIGAGAME","KXMLSCUP","KXJLEAGUEGAME","KXURYPDGAME","KXWCROUND","KXBUNDESLIGATOP4","KXLIGAMXSPREAD","KXBRASILEIROGAME","KXLIGAMXGAME","KXUCLBTTS","KXALLSVENSKANGAME","KXBUNDESLIGA1H","KXEFLCHAMPIONSHIP","KXUCLSPREAD","KXLIGUE1TOTAL","KXBRASILEIROTOTAL","KXSOCCERPLAYCRON","KXVENFUTVEGAME","KXLALIGATOP4","KXEFLCHAMPIONSHIPGAME","KXPERLIGA1","KXEKSTRAKLASAGAME","KXMLSGAME","KXMLSWEST","KXWCMESSIRONALDO","KXAPFDDH","KXJOINCLUB","KXLALIGA1H","KXWINSTREAKMANU","KXUCL","KXSLGREECE","KXBRASILEIRO","KXHNLGAME","KXSERIEA","KXSERIEABTTS","KXSWISSLEAGUEGAME","KXEREDIVISIEGAME","KXWCIRAN","KXLALIGA","KXALEAGUEGAME","KXCONCACAFCCUPGAME","KXBELGIANPLGAME","KXBUNDESLIGA","KXUEL","KXBUNDESLIGARELEGATION","KXLIGUE1TOP4","KXEPLTOP2","KXUECL","KXCHLLDP","KXBUNDESLIGABTTS","KXWCGROUPQUAL","KXBUNDESLIGAGAME","KXUCLFINALIST","KXSUPERLIGGAME","KXBRASILEIROTOPX","KXLIGAPORTUGAL","KXUCLRO4","KXKNVBCUP","KXCOPADELREY","KXBUNDESLIGASPREAD","KXLALIGA2GAME","KXCHNSLGAME","KXMLSSPREAD","KXSERIEATOP4","KXTEAMSINUCL","KXBRASILEIROSPREAD","KXLIGUE1GAME","KXDENSUPERLIGA","KXMLSTOTAL","KXLALIGAGAME","KXNEXTMANAGERMANU","KXPFAPOY","KXLIGUE1","KXMLSEAST","KXUCLTOTAL","KXWCLOCATION","KXEPLRELEGATION","KXUELGAME","KXECULPGAME","KXUELTOTAL","KXEREDIVISIE"]),
    ("🏀","Basketball",["KXNBAEFINMVP","KXLEADERNBABLK","KXNBAMVP","KXNBASIXTH","KXCITYNBAEXPAND","KXBSLGAME","KXBBLGAME","KXNBACLUTCH","KXNBADRAFTPICK","KXTEAMSINNBAEF","KXSONICS","KXNBADPOY","KXNBAWINS","KXNBALOTTERYODDS","KXTEAMSINNBAF","KXNBADRAFTCOMP","KXNBA","KXWNBADRAFT1","KXNBAMATCHUP","KXBBSERIEAGAME","KXNBAWFINMVP","KXLEADERNBAAST","KXNBASEATTLE","KXMARMAD","KXNBAPLAYOFF","KXNBADRAFTTOP","KXWNBADRAFTTOP3","KXISLGAME","KXNBA2NDTEAMDEF","KXNBA1STTEAMDEF","KXNBAMIMP","KXLEADERNBAREB","KXABAGAME","KXNBAFINMVP","KXACBGAME","KXWNBADELAY","KXLEADERNBASTL","KXNCAAMBNEXTCOACH","KXNBASOUTHWEST","KXNBATOPPICK","KXCBAGAME","KXNBAATLANTIC","KXNBAEAST1SEED","KXJBLEAGUEGAME","KXNBAROY","KXSTEPHDEAL","KXNBAEAST","KXNBA1STTEAM","KXNBACOY","KXNBA2NDTEAM","KXLEADERNBA3PT","KXLBJRETIRE","KXNBAWEST","KXSPORTSOWNERLBJ","KXNEXTTEAMNBA","KXWNBAGAMESPLAYED","KXNBASOUTHEAST","KXNBADRAFTCAT","KXNBA3RDTEAM","KXNBAPACIFIC","KXARGLNBGAME","KXQUADRUPLEDOUBLE","KXNBACENTRAL","KXRECORDNBABEST","KXNBANORTHWEST","KXLNBELITEGAME","KXNBAWEST1SEED","KXNBAPLAYIN","KXLEADERNBAPTS","KXEUROLEAGUEGAME","KXNBATEAM","KXNBADRAFT1"]),
    ("⚾","Baseball",["KXMLBEOTY","KXMLBGAME","KXNCAABBGS","KXMLBNLROTY","KXMLBWINS-CWS","KXMLBWINS-SF","KXMLBALROTY","KXMLBALWEST","KXMLBNLMOTY","KXMLBWINS-PHI","KXMLBWINS-PIT","KXMLB","KXMLBWINS-NYY","KXMLBWINS-LAA","KXLEADERMLBSTEALS","KXMLBSTATCOUNT","KXMLBTRADE","KXMLBNLRELOTY","KXLEADERMLBDOUBLES","KXMLBWINS-TEX","KXMLBWINS-CHC","KXLEADERMLBERA","KXMLBWINS-DET","KXMLBWINS-MIN","KXMLBWINS-SD","KXMLBRFI","KXMLBWINS-TB","KXMLBLSTREAK","KXMLBNLEAST","KXMLBWINS-BAL","KXMLBWINS-NYM","KXMLBNLMVP","KXLEADERMLBTRIPLES","KXMLBPLAYOFFS","KXMLBWINS-CLE","KXMLBSEASONHR","KXMLBWINS-WSH","KXMLBAL","KXMLBWINS-KC","KXLEADERMLBWINS","KXMLBNLWEST","KXMLBWINS-MIA","KXMLBBESTRECORD","KXMLBWINS-MIL","KXLEADERMLBRBI","KXMLBWINS-HOU","KXMLBSTAT","KXMLBALHAARON","KXLEADERMLBAVG","KXMLBALMVP","KXMLBWINS-TOR","KXMLBWINS-ATL","KXMLBNLCPOTY","KXMLBWINS-AZ","KXLEADERMLBOPS","KXMLBALCPOTY","KXMLBWINS-COL","KXMLBWINS-LAD","KXMLBWINS-ATH","KXMLBWINS-CIN","KXMLBNLCENT","KXMLBNL","KXNCAABASEBALL","KXLEADERMLBRUNS","KXMLBWINS-STL","KXMLBWINS-SEA","KXMLBALMOTY","KXMLBALCY","KXTEAMSINWS","KXMLBNLCY","KXMLBALRELOTY","KXMLBNLHAARON","KXLEADERMLBHITS","KXLEADERMLBHR","KXMLBWORSTRECORD","KXMLBWINS-BOS","KXMLBALCENT","KXMLBALEAST"]),
    ("🏈","Football",["KXNFLNFCNORTH","KXNFLDRAFTWR","KXUFLGAME","KXSB","KXNFLAFCEAST","KXNFLOPOTY","KXNCAAFCONF","KXHEISMAN","KXNEXTTEAMNFL","KXLEADERNFLSACKS","KXNCAAFCUSA","KXNFLCOTY","KXNCAAFAPRANK","KXLEADERNFLINT","KXNFLDRAFTDB","KXNCAAFSBELT","KXNCAAFACC","KXNFLDPOTY","KXNFLAFCSOUTH","KXNFLNFCWEST","KXNCAAFSEC","KXLEADERNFLPTDS","KXNFLPRIMETIME","KXCOACHOUTNFL","KXNCAAFAAC","KXDONATEMRBEAST","KXLEADERNFLRUSHYDS","KXNCAAFPLAYOFF","KXNCAAFMWC","KXNFLDRAFTTE","KXNCAAFB10","KXNCAAFMAC","KXNFLDRAFTQB","KXNFLNFCEAST","KXNFLDRAFTOL","KXKELCERETIRE","KXNFLNFCCHAMP","KXCOACHOUTNCAAFB","KXNFLDRAFTEDGE","KXNFLDRAFTTEAM","KXSTARTINGQBWEEK1","KXLEADERNFLRYDS","KXSORONDO","KXNFLDRAFTLB","KXARODGRETIRE","KXLEADERNFLRUSHTDS","KXNCAAF","KXNFLOROTY","KXNFLTEAM1POS","KXNFLAFCNORTH","KXNFLDROTY","KXNFLMVP","KXNFLDRAFT1","KXNCAAFB12","KXNFLDRAFTTOP","KXNFLNFCSOUTH","KXNFLDRAFT1ST","KXLEADERNFLPYDS","KXNFLAFCCHAMP","KXRELOCATIONCHI","KX1STHOMEGAME","KXNFLDRAFTRB","KXNCAAFFINALIST","KXLEADERNFLRTDS","KXNFLAFCWEST","KXNFLDRAFTPICK","KXNFLDRAFTDT","KXNCAAFCOTY","KXNCAAFPAC12","KXNFLPLAYOFF","KXNCAAFUNDEFEATED","KXNFLTRADE"]),
    ("🏒","Hockey",["KXNHLRICHARD","KXNHLEAST","KXCANADACUP","KXNHLADAMS","KXNHLPLAYOFF","KXNHLSPREAD","KXNHL","KXNHLNORRIS","KXNHLTOTAL","KXNHLPRES","KXNHLCALDER","KXNCAAHOCKEY","KXNHLROSS","KXNHLCENTRAL","KXNHLATLANTIC","KXNHLMETROPOLITAN","KXAHLGAME","KXTEAMSINSC","KXNHLVEZINA","KXNHLHART","KXNHLPACIFIC","KXNHLWEST","KXNHLGAME"]),
    ("🎾","Tennis",[
        "KXMCMMEN","KXFOWOMEN","KXGRANDSLAM","KXWTAGRANDSLAM","KXGOLFTENNISMAJORS",
        "KXWTASERENA","KXATPGRANDSLAMFIELD","KXGRANDSLAMJFONSECA","KXFOMEN",
        "KXATPGRANDSLAM","KXATP1RANK","KXATPRANK","KXATPFINALS","KXWTAFINALS",
        "KXATPNEXTGEN","KXTENNISMAJORDJOKOVIC","KXALCARAZCOACH","KXTENNISGRANDSLAM",
        # Individual match series
        "KXATPMC","KXATPMCO","KXATPMAD","KXATPMIA","KXATPIWO","KXATPAMT","KXATPIT","KXATPWDDF",
        "KXATPGAME","KXATPMATCH","KXATPGAMESPREAD","KXATPGAMETOTAL","KXATPGSPREAD",
        "KXATPSETWINNER","KXATPANYSET","KXATPEXACTMATCH","KXATPDOUBLES","KXATPCHALLENGERMATCH",
        "KXCHALLENGERMATCH","KXMCMEN",
        "KXWTAMAD","KXWTAMIA","KXWTAIWO","KXWTAATX","KXWTAMOA","KXWTAIT","KXWTADDF",
        "KXWTAGAME","KXWTAMATCH","KXWTADOUBLES","KXWTACHALLENGERMATCH",
        "KXFOPENMENSINGLE","KXFOPENWMENSINGLE","KXAOMENSINGLES","KXAOWOMEN",
        "KXUSOMENSINGLES","KXUSOWOMENSINGLES","KXROMENSSINGLES","KXROMENSDOUBLES",
        "KXWMENSINGLES","KXWWOMENSINGLES","KXIWMEN","KXIWWOMEN","KXIWMENDOUBLES",
        "KXMOMEN","KXMOWOMEN","KXDDFMENSINGLES","KXDDFWOMENSINGLES",
        "KXQEMOMENSSINGLES","KXQOWOMENSINGLES","KXFOMENSINGLES","KXFOWOMENSINGLES",
        "KXO13MENSINGLES",
        "KXUNITEDCUP","KXUNITEDCUPMATCH","KXUNITEDCUPADVANCE",
        "KXDAVISCUP","KXDAVISCUPMATCH","KXDAVISCUPADVANCE",
        "KXLAVERCUP",
        "KXSIXKINGSSLAM","KXSIXKINGSMATCH","KXSIXKINGSQUARTER","KXSIXKINGSSEMI","KXSIXKINGSSLAMMATCH",
        "KXTENNISEXHIBITION","KXEXHIBITIONMEN","KXEXHIBITIONWOMEN",
        "KXBATTLEOFSEXES","KXBATTLEOFSEXESSET",
        "KXITFMATCH","KXITFWMATCH",
    ]),
    ("⛳","Golf",["KXPGAR3LEAD","KXBRYSONCOURSERECORDS","KXPGAR1LEAD","KXPGAMAJORTOP10","KXPGAR2LEAD","KXPGA5BALL","KXPGAEAGLE","KXPGAHOLEINONE","KXGOLFMAJORS","KXPGAMAJORWIN","KXRYDERCUPCAPTAIN","KXPGAPLAYERCAT","KXPGAR3TOP5","KXPGABOGEYFREE","KXPGATOUR","KXPGACURRY","KXPGATOP40","KXGOLFTENNISMAJORS","KXPGAPLAYOFF","KXPGATIGER","KXPGASOLHEIM","KXPGAMASTERS","KXPGAH2H","KXPGATOP10","KXSCOTTIESLAM","KXPGARYDER","KXPGACUTLINE","KXPGAR3TOP10","KXPGATOP5","KXPGATOP20","KXPGAWINNERREGION","KXPGALOWSCORE"]),
    ("🥊","MMA",["KXUFCFLYWEIGHTTITLE","KXUFCBANTAMWEIGHTTITLE","KXUFCFIGHT","KXUFCMIDDLEWEIGHTTITLE","KXUFCHEAVYWEIGHTTITLE","KXUFCLIGHTWEIGHTTITLE","KXUFCFEATHERWEIGHTTITLE","KXUFCLHEAVYWEIGHTTITLE","KXMCGREGORFIGHTNEXT","KXUFCWELTERWEIGHTTITLE"]),
    ("🏏","Cricket",["KXIPLGAME","KXPSLGAME","KXPSL","KXIPL"]),
    ("🎮","Esports",["KXVALORANTMAP","KXLOLGAME","KXVALORANTGAME","KXR6GAME","KXLOLMAP","KXLOLTOTALMAPS"]),
    ("🏎️","Motorsport",["KXF1RACE","KXF1RACEPODIUM","KXNASCARTOP10","KXMOTOGPTEAMS","KXNASCARTOP20","KXF1OCCUR","KXINDYCARSERIES","KXNASCARTOP5","KXNASCARAUTOPARTSSERIES","KXF1TOP5","KXMOTOGP","KXF1FASTLAP","KXF1CONSTRUCTORS","KXNASCARTOP3","KXNASCARRACE","KXF1RETIRE","KXNASCARTRUCKSERIES","KXF1","KXNASCARCUPSERIES","KXF1TOP10"]),
    ("🥊","Boxing",["KXWBCWELTERWEIGHTTITLE","KXWBCMIDDLEWEIGHTTITLE","KXBOXING","KXWBCFEATHERWEIGHTTITLE","KXFLOYDTYSONFIGHT","KXWBCBANTAMWEIGHTTITLE","KXWBCLIGHTWEIGHTTITLE","KXWBCHEAVYWEIGHTTITLE","KXWBCCRUISERWEIGHTTITLE","KXWBCFLYWEIGHTTITLE"]),
    ("♟️","Chess",["KXCHESSWORLDCHAMPION","KXCHESSCANDIDATES"]),
    ("🏉","Rugby",["KXPREMCHAMP","KXRUGBYNRLMATCH","KXFRA14CHAMP","KXSLRCHAMP","KXNRLCHAMP"]),
    ("🥍","Lacrosse",["KXLAXTEWAARATON","KXNCAAMLAXGAME","KXNCAALAXFINAL"]),
    ("🎯","Darts",["KXPREMDARTS"]),
    ("🏉","Aussie Rules",["KXAFLGAME"]),
    ("⛵","Other",["KXSAILGP"]),
]

SPORT_ICON = {name: ic for ic, name, _ in SPORT_TAGS}
SERIES_TO_SPORT = {}
for ic, sname, tickers in SPORT_TAGS:
    for t in tickers:
        SERIES_TO_SPORT[t] = sname

def detect_sport(series_ticker):
    return SERIES_TO_SPORT.get(str(series_ticker).upper(), "")

SOCCER_COMP_MAP = {
    "KXEPL":"EPL","KXPREMIERLEAGUE":"EPL","KXARSENALCUPS":"EPL","KXPFAPOY":"EPL","KXNEXTMANAGERMANU":"EPL","KXWINSTREAKMANU":"EPL",
    "KXUCLGAME":"Champions League","KXUCL1H":"Champions League","KXUCLSPREAD":"Champions League","KXUCLTOTAL":"Champions League","KXUCLBTTS":"Champions League","KXUCL":"Champions League","KXUCLFINALIST":"Champions League","KXUCLRO4":"Champions League","KXUCLW":"Champions League","KXLEADERUCLGOALS":"Champions League","KXTEAMSINUCL":"Champions League",
    "KXUELGAME":"Europa League","KXUELSPREAD":"Europa League","KXUELTOTAL":"Europa League","KXUEL":"Europa League",
    "KXUECL":"Conference League",
    "KXLALIGAGAME":"La Liga","KXLALIGA1H":"La Liga","KXLALIGASPREAD":"La Liga","KXLALIGATOTAL":"La Liga","KXLALIGABTTS":"La Liga","KXLALIGA":"La Liga","KXLALIGATOP4":"La Liga","KXLALIGARELEGATION":"La Liga","KXLALIGA2GAME":"La Liga",
    "KXSERIEAGAME":"Serie A","KXSERIEA1H":"Serie A","KXSERIEASPREAD":"Serie A","KXSERIEATOTAL":"Serie A","KXSERIEABTTS":"Serie A","KXSERIEA":"Serie A","KXSERIEATOP4":"Serie A","KXSERIEARELEGATION":"Serie A","KXSERIEBGAME":"Serie A",
    "KXBUNDESLIGAGAME":"Bundesliga","KXBUNDESLIGA1H":"Bundesliga","KXBUNDESLIGASPREAD":"Bundesliga","KXBUNDESLIGATOTAL":"Bundesliga","KXBUNDESLIGABTTS":"Bundesliga","KXBUNDESLIGA":"Bundesliga","KXBUNDESLIGATOP4":"Bundesliga","KXBUNDESLIGARELEGATION":"Bundesliga","KXBUNDESLIGA2GAME":"Bundesliga",
    "KXLIGUE1GAME":"Ligue 1","KXLIGUE11H":"Ligue 1","KXLIGUE1SPREAD":"Ligue 1","KXLIGUE1TOTAL":"Ligue 1","KXLIGUE1BTTS":"Ligue 1","KXLIGUE1":"Ligue 1","KXLIGUE1TOP4":"Ligue 1","KXLIGUE1RELEGATION":"Ligue 1",
    "KXMLSGAME":"MLS","KXMLSSPREAD":"MLS","KXMLSTOTAL":"MLS","KXMLSBTTS":"MLS","KXMLSCUP":"MLS","KXMLSEAST":"MLS","KXMLSWEST":"MLS",
    "KXLIGAMXGAME":"Liga MX","KXLIGAMXSPREAD":"Liga MX","KXLIGAMXTOTAL":"Liga MX","KXLIGAMX":"Liga MX",
    "KXBRASILEIROGAME":"Brasileiro","KXBRASILEIROSPREAD":"Brasileiro","KXBRASILEIROTOTAL":"Brasileiro","KXBRASILEIRO":"Brasileiro","KXBRASILEIROTOPX":"Brasileiro",
    "KXWCGAME":"World Cup","KXWCROUND":"World Cup","KXWCGROUPWIN":"World Cup","KXWCGROUPQUAL":"World Cup","KXWCGOALLEADER":"World Cup","KXWCMESSIRONALDO":"World Cup","KXWCLOCATION":"World Cup","KXWCIRAN":"World Cup","KXWCSQUAD":"World Cup","KXMENWORLDCUP":"World Cup","KXSOCCERPLAYMESSI":"World Cup","KXSOCCERPLAYCRON":"World Cup","KXFIFAUSPULL":"World Cup",
    "KXSAUDIPLGAME":"Saudi Pro League","KXSAUDIPLSPREAD":"Saudi Pro League","KXSAUDIPLTOTAL":"Saudi Pro League",
    "KXLIGAPORTUGALGAME":"Liga Portugal","KXLIGAPORTUGAL":"Liga Portugal",
    "KXEREDIVISIEGAME":"Eredivisie","KXEREDIVISIE":"Eredivisie",
    "KXCOPADELREY":"Copa del Rey","KXDFBPOKAL":"DFB Pokal","KXFACUP":"FA Cup","KXCOPPAITALIA":"Coppa Italia",
    "KXEFLCHAMPIONSHIPGAME":"EFL Championship","KXEFLCHAMPIONSHIP":"EFL Championship","KXEFLPROMO":"EFL Championship",
    "KXSUPERLIGGAME":"Super Lig","KXSUPERLIG":"Super Lig",
    "KXCONCACAFCCUPGAME":"CONCACAF","KXUSLGAME":"USL","KXUSL":"USL",
    "KXSCOTTISHPREMGAME":"Scottish Prem",
    "KXEKSTRAKLASAGAME":"Ekstraklasa","KXEKSTRAKLASA":"Ekstraklasa",
    "KXALEAGUEGAME":"A-League","KXALEAGUESPREAD":"A-League","KXALEAGUETOTAL":"A-League",
    "KXKLEAGUEGAME":"K League","KXKLEAGUE":"K League",
    "KXJLEAGUEGAME":"J League","KXCHNSLGAME":"Chinese SL","KXCHNSL":"Chinese SL",
    "KXALLSVENSKANGAME":"Allsvenskan","KXDENSUPERLIGAGAME":"Danish SL","KXDENSUPERLIGA":"Danish SL",
    "KXSWISSLEAGUEGAME":"Swiss League","KXARGPREMDIVGAME":"Argentinian","KXDIMAYORGAME":"Colombian",
    "KXURYPDGAME":"Uruguayan","KXURYPD":"Uruguayan","KXECULPGAME":"Ecuador LigaPro","KXECULP":"Ecuador LigaPro",
    "KXVENFUTVEGAME":"Venezuelan","KXVENFUTVE":"Venezuelan","KXCHLLDPGAME":"Chilean","KXCHLLDP":"Chilean",
    "KXAPFDDHGAME":"APF","KXAPFDDH":"APF","KXSLGREECE":"Greek SL",
    "KXTHAIL1GAME":"Thai League","KXTHAIL1":"Thai League","KXEGYPLGAME":"Egyptian PL",
    "KXHNLGAME":"HNL Croatia","KXBELGIANPLGAME":"Belgian Pro","KXBELGIANPL":"Belgian Pro",
    "KXPERLIGA1":"Peruvian L1","KXKNVBCUP":"KNVB Cup",
    "KXLAMINEYAMAL":"Transfer/Other","KXBALLONDOR":"Awards","KXSOCCERTRANSFER":"Transfer/Other",
    "KXJOINLEAGUE":"Transfer/Other","KXJOINRONALDO":"Transfer/Other","KXJOINCLUB":"Transfer/Other",
}

def get_soccer_comp(series):
    s = str(series).upper()
    if s in SOCCER_COMP_MAP:
        return SOCCER_COMP_MAP[s]
    for prefix, comp in SOCCER_COMP_MAP.items():
        if s.startswith(prefix):
            return comp
    return "Other"

def safe_date(val):
    try:
        if val is None or val == "": return None
        if isinstance(val, date) and not isinstance(val, pd.Timestamp): return val
        ts = pd.to_datetime(val, utc=True)
        if pd.isna(ts): return None
        return ts.to_pydatetime().astimezone(UTC).date()
    except: return None

def fmt_date(d):
    try: return d.strftime("%b %d") if d else "Open"
    except: return "Open"

def fmt_pct(v):
    try:
        f = float(v)
        return f"{int(round(f*100)) if f<=1.0 else int(round(f))}%"
    except: return "—"

@st.cache_resource
def get_client():
    try:
        from kalshi_python_sync import Configuration, KalshiClient
        key_id  = st.secrets["KALSHI_API_KEY_ID"]
        key_str = st.secrets["KALSHI_PRIVATE_KEY"]
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".pem") as f:
            f.write(key_str); pem = f.name
        cfg = Configuration()
        cfg.api_key_id = key_id
        cfg.private_key_pem_path = pem
        return KalshiClient(cfg)
    except Exception as e:
        st.error(f"❌ {e}"); st.stop()

client = get_client()

def paginate(with_markets=False, category=None, series_ticker=None, max_pages=30):
    events, cursor = [], None
    for _ in range(max_pages):
        try:
            kw = {"limit": 200, "status": "open"}
            if with_markets:  kw["with_nested_markets"] = True
            if category:      kw["category"] = category
            if series_ticker: kw["series_ticker"] = series_ticker
            if cursor:        kw["cursor"] = cursor
            resp  = client.get_events(**kw).to_dict()
            batch = resp.get("events", [])
            if not batch: break
            events.extend(batch)
            cursor = resp.get("cursor") or resp.get("next_cursor")
            if not cursor: break
            time.sleep(0.1)
        except Exception as e:
            if "429" in str(e): time.sleep(3)
            else: break
    return events

@st.cache_data(ttl=1800)
def fetch_all():
    prog = st.progress(0, text="Step 1 — Fetching all events…")
    all_ev = paginate(with_markets=False, max_pages=30)
    ev_map = {e["event_ticker"]: e for e in all_ev}
    prog.progress(0.35, text=f"{len(all_ev)} events found. Step 2 — Fetching sports odds…")

    sport_events = paginate(with_markets=True, category="Sports", max_pages=30)
    for e in sport_events:
        t = e.get("event_ticker", "")
        if not t: continue
        if t not in ev_map or (e.get("markets") and not ev_map.get(t, {}).get("markets")):
            ev_map[t] = e

    prog.progress(0.85, text="Building dataframe…")
    combined = list(ev_map.values())
    if not combined:
        prog.empty(); return pd.DataFrame()

    df = pd.DataFrame(combined)
    df["category"]   = df.get("category", pd.Series("Other", index=df.index)).fillna("Other").str.strip()
    df["_series"]    = df.get("series_ticker", pd.Series("", index=df.index)).fillna("").str.upper()
    df["_sport"]     = df["_series"].apply(detect_sport)
    df["_is_sport"]  = df["_sport"] != ""
    df["_soccer_comp"] = df.apply(
        lambda r: get_soccer_comp(r["_series"]) if r["_sport"] == "Soccer" else "", axis=1
    )

    if "markets" not in df.columns:
        df["markets"] = [[] for _ in range(len(df))]
    else:
        df["markets"] = df["markets"].apply(lambda x: x if isinstance(x, list) else [])

    def extract(row):
        mkts = row.get("markets")
        if not isinstance(mkts, list) or len(mkts) == 0:
            return "—", "—", None
        m = mkts[0]
        yes = fmt_pct(m.get("yes_bid_dollars") or m.get("yes_bid"))
        no  = fmt_pct(m.get("no_bid_dollars")  or m.get("no_bid"))
        close = None
        for mk in mkts:
            d = safe_date(mk.get("close_time"))
            if d and (close is None or d < close): close = d
        return yes, no, close

    info = df.apply(extract, axis=1, result_type="expand")
    df["_yes"] = info[0]; df["_no"] = info[1]; df["_mkt_dt"] = info[2]

    def best_dt(row):
        for col in ["strike_date","close_time","end_date","expiration_time"]:
            d = safe_date(row.get(col))
            if d: return d
        return row.get("_mkt_dt")

    df["_sort_dt"]    = df.apply(best_dt, axis=1)
    df["_display_dt"] = df["_sort_dt"].apply(fmt_date)
    prog.progress(1.0); prog.empty()
    return df

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📡 Kalshi Terminal")
    search = st.text_input("🔍 Search", placeholder="team, market, keyword…")
    st.markdown("---")
    st.markdown("**📅 Date**")
    today = date.today()
    date_mode = st.radio("Show", ["All dates","Today","Tomorrow","This week","Custom range"], index=0)
    d_start = d_end = None
    if date_mode == "Today":       d_start = d_end = today
    elif date_mode == "Tomorrow":  d_start = d_end = today + timedelta(days=1)
    elif date_mode == "This week": d_start, d_end = today, today + timedelta(days=6)
    elif date_mode == "Custom range":
        d_start = st.date_input("From", value=today)
        d_end   = st.date_input("To",   value=today + timedelta(days=7))
    include_no_date = st.checkbox("Include events with no date", value=True)
    st.markdown("---")
    sort_by = st.radio("↕️ Sort", ["Earliest first","Latest first","Default"], index=0)
    st.markdown("---")
    if st.button("🔄 Refresh"): fetch_all.clear(); st.rerun()
    st.caption("Cached 30 min.")

# ── Main ──────────────────────────────────────────────────────────────────────
st.title("📡 Kalshi Markets Terminal")
with st.spinner("Loading…"):
    df = fetch_all()

if df.empty:
    st.error("No data. Check API credentials."); st.stop()

# ── Filter ────────────────────────────────────────────────────────────────────
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
    has = filtered["_sort_dt"].notna()
    dated, undated = filtered[has].copy(), filtered[~has].copy()
    dated["_sk"] = dated["_sort_dt"].apply(lambda d: str(d) if d else "9999")
    dated = dated.sort_values("_sk", ascending=asc).drop(columns=["_sk"])
    filtered = pd.concat([dated, undated], ignore_index=True)

sport_count = int(df["_is_sport"].sum())
st.markdown(f"""<div class="metric-strip">
  <div class="metric-box"><div class="metric-label">Total markets</div><div class="metric-value">{len(df)}</div></div>
  <div class="metric-box"><div class="metric-label">Sports</div><div class="metric-value">{sport_count}</div></div>
  <div class="metric-box"><div class="metric-label">Showing</div><div class="metric-value">{len(filtered)}</div></div>
</div>""", unsafe_allow_html=True)

# ── Render helpers ─────────────────────────────────────────────────────────────
def render_cards(data):
    if data.empty:
        st.markdown('<div class="empty-state">No markets match your filters.</div>', unsafe_allow_html=True)
        return
    html = '<div class="card-grid">'
    for _, row in data.iterrows():
        try:
            ticker  = str(row.get("event_ticker","")).upper()
            cat     = str(row.get("category","Other"))
            title   = str(row.get("title","Unknown"))[:90]
            sport   = str(row.get("_sport",""))
            base_ic, pill = CAT_META.get(cat, ("📊","pill-default"))
            icon    = SPORT_ICON.get(sport, base_ic) if sport else base_ic
            label   = (sport[:16] if sport else cat[:16])
            dt      = str(row.get("_display_dt","Open"))
            yes     = str(row.get("_yes","—"))
            no      = str(row.get("_no","—"))
            html += f"""<div class="market-card">
<div class="card-top"><span class="cat-pill {pill}">{label}</span><span class="date-text">📅 {dt}</span></div>
<span class="card-icon">{icon}</span>
<div class="card-title">{title}</div>
<div class="card-footer"><span class="ticker-text">{ticker}</span>
<div class="odds-row">
<div class="odds-yes"><div class="odds-label">YES</div><div class="odds-price-yes">{yes}</div></div>
<div class="odds-no"><div class="odds-label">NO</div><div class="odds-price-no">{no}</div></div>
</div></div></div>"""
        except: continue
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_subtag_tabs(sport_df, sport):
    """Render sub-category tabs for any sport that has SPORT_SUBTAGS defined."""
    subtags = SPORT_SUBTAGS.get(sport, [])
    if not subtags:
        render_cards(sport_df)
        return

    # Only show tabs whose search terms actually match something in this data
    def matches(row, terms):
        title   = str(row.get("title","")).lower()
        ticker  = str(row.get("event_ticker","")).upper()
        series  = str(row.get("_series","")).upper()
        for t in terms:
            tu = t.upper()
            if tu in ticker or tu in series or t.lower() in title:
                return True
        return False

    present_subtags = []
    for label, terms in subtags:
        mask = sport_df.apply(lambda r: matches(r, terms), axis=1)
        if mask.any():
            present_subtags.append((label, terms))

    if not present_subtags:
        render_cards(sport_df)
        return

    tab_labels = ["All"] + [label for label, _ in present_subtags]
    tabs = st.tabs(tab_labels)
    with tabs[0]:
        render_cards(sport_df)
    for i, (label, terms) in enumerate(present_subtags):
        with tabs[i + 1]:
            mask = sport_df.apply(lambda r: matches(r, terms), axis=1)
            render_cards(sport_df[mask])


def render_sport_tabs(sdf):
    present = [name for _, name, _ in SPORT_TAGS if name in sdf["_sport"].values]
    if not present:
        render_cards(sdf); return

    labels   = ["🏟️ All"] + [f"{SPORT_ICON[s]} {s}" for s in present]
    top_tabs = st.tabs(labels)

    with top_tabs[0]:
        render_cards(sdf)

    for i, sport in enumerate(present):
        with top_tabs[i + 1]:
            sport_df = sdf[sdf["_sport"] == sport].copy()

            if sport == "Soccer":
                # Soccer uses competition map (existing logic)
                comps_present = sorted([c for c in sport_df["_soccer_comp"].unique() if c and c != "Other"])
                has_other = (sport_df["_soccer_comp"] == "Other").any()
                comp_list = comps_present + (["Other"] if has_other else [])
                if not comp_list:
                    render_cards(sport_df)
                else:
                    ctabs = st.tabs(["All"] + comp_list)
                    with ctabs[0]:
                        render_cards(sport_df)
                    for j, comp in enumerate(comp_list):
                        with ctabs[j + 1]:
                            render_cards(sport_df[sport_df["_soccer_comp"] == comp])
            else:
                # All other sports use SPORT_SUBTAGS
                render_subtag_tabs(sport_df, sport)


def render_tag_tabs(cat_df, cat):
    tags = CAT_TAGS.get(cat, [])
    if not tags:
        render_cards(cat_df); return
    ttabs = st.tabs(["All"] + tags)
    for i, ttab in enumerate(ttabs):
        with ttab:
            if i == 0: render_cards(cat_df)
            else:
                tag = tags[i-1]
                tag_df = cat_df[
                    cat_df["title"].str.contains(tag, case=False, na=False, regex=False) |
                    cat_df["event_ticker"].str.contains(tag.replace(" ","").upper(), na=False)
                ]
                render_cards(tag_df)

present_cats = ["All"] + [c for c in TOP_CATS
    if (c=="Sports" and sport_count>0) or (c!="Sports" and c in df["category"].values)]
top_tabs = st.tabs(present_cats)
for i, tab in enumerate(top_tabs):
    with tab:
        cat = present_cats[i]
        if cat == "All":       render_cards(filtered)
        elif cat == "Sports":  render_sport_tabs(filtered[filtered["_is_sport"]].copy())
        else:                  render_tag_tabs(filtered[filtered["category"]==cat].copy(), cat)

st.markdown("<hr><p style='text-align:center;color:#1f2937;font-size:11px;'>KALSHI TERMINAL · CACHED 30 MIN · NOT FINANCIAL ADVICE</p>", unsafe_allow_html=True)
