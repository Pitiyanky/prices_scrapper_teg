import os
from dotenv import load_dotenv

load_dotenv()

CHROME_BROWSER_PATH = os.getenv("CHROME_BROWSER_PATH", r"driver/chrome/chrome")
CHROME_DRIVER_EXECUTABLE_PATH = os.getenv("CHROME_DRIVER_EXECUTABLE_PATH", r"driver/chrome-driver/chromedriver")
URL_KROMI_VIVERES = "https://www.kromionline.com/Products.php?cat=VIV"
URL_KALEA_MARKET_CAT = "https://kaleamarket.com/purchases;category=SYujECu7g0UJamAYdCTu"

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "8090")
DB_NAME = os.getenv("DB_NAME", "scraping_data")
DB_USER = os.getenv("DB_USER", "Pitiyanky")
DB_PASSWORD = os.getenv("DB_PASSWORD", "1234")
DB_CONFIG = {
    "host": DB_HOST,
    "port": DB_PORT,
    "dbname": DB_NAME,
    "user": DB_USER,
    "password": DB_PASSWORD
}

DB_CONNECTION_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
SCORE_THRESHOLD = 85
CODIGO_PAIS_FESTIVOS = 'VE'

MARCAS_CONOCIDAS = ["ACE","P.A.N.","Juana","Mary","Primor","Ronco","Capri","Vatel","Mazeite","Mavesa","Heinz","Pampero",
                    "La Giralda","Knorr","Maggi","La Comadre","Iberia","Eveba","Margarita","Paraguaná","Diablitos Underwood","Paisa",
                    "Torondoy","La Campiña","Mi Vaca","Zuli Lac","Plumrose","Oscar Mayer","Hermo","Arichuna","La Montserratina","Savoy",
                    "Toronto","Carré","Samba","Cocosette","Susy","Cri-Cri","Galak","St. Moritz","Flaquito","El Rey","Pirulin","Nucita","Ovomaltina",
                    "Puig","Nabisco","Oreo","Club Social","Ritz","Toddy","Marilú","Jack's","Pepito","Cheese Tris","Doritos","Ruffles","Lays","Cheetos",
                    "Tostitos","NatuChips","Coca-Cola","Pepsi","Golden","Frescolita","Chinotto","Hit","Malta Polar","Maltín Polar","Yukery","Frica",
                    "Nestea","Fama de América","Café Madrid","San Antonio","El Peñón","Tío Rico","EFE","Cacique","Santa Teresa","Diplomático","Zulia",
                    "Regional","Solera","Rikesa","Cheez Whiz","Dalvito","Montalbán","La Pastora","Doña Emilia","La Lucha","Quaker","Kellogg's","Nestlé",
                    "Robin Hood","Deyavú","Maizina Americana","Cerelac","Avelina","Milani","Allegri","La Parmesana","A-1","Santoni","Sindoni","Pantera",
                    "Kiko","Campestre","Mirasol","Branca","Coppelia","Los Tres Cochinitos","Fritz","Renna","McCormick","Del Monte","French's","Adobo El Rey",
                    "Carmencita","El Faro","Sazonaltodo","Atún Bahía","Sardinas La Sirena","Albeca","Santa Bárbara","Flor de Aragua","Los Frailes",
                    "Lácteos Táchira","Kraft","Bufalinda","Camprolac","Los Andes","Charvenca","Ital-deli","Fiesta","Mister Pollo","La Rosa","Caledonia",
                    "Danibisk","Renata","Galletón","Bon Bon Bum","Supercoco","Bolibomba","La Marcona","Kron","Royal Crown Cola","Lipton","California","Riko Malt",
                    "Nesquik","Caroreña","Pomar","Ocumare","Fleishmann","Royal","Nevazucar","Gerber","Nestum","Dog Chow","Cat Chow","Perrarina","Gatarina",
                    "Protican","Super Can","K-NINA","Chunky","4D","Fragolate","Crema Paraíso","Gold Star","Glup","Swing","Amanecer","Flor de Patria","Café Venezuela"
                    ,"La Protectora","Bodegas Lazo","Backels","Agros","Mr. Pops","A-1","Glory","Don Pancho","Mimesa","La Torre del Oro","La Vencedora","Sabroso",
                    "Yeli","Las Cumbres","La Pradera","Suizo","Castelo Branco","Frimaca","Tosty","Pepinuts","K-Listo","Evercrisp","Carabobo","Sorbeticos","Herencia Divina",
                    "Cacao de Origen","Mantuano","Bonella","La Vienesa","Orinoquia","Tampico","Superior","Wilton","Chocono","Avícola de Occidente","Granja La Caridad",
                    "Enfamil","Pro Pac","Alimentos La Giralda","Galletera Trigo de Oro","La Especial","Manicería San Jorge","Salsas D'Addario","Alimentos Nina",
                    "Maltín Polar Light","Solera Light","Polar Pilsen","Polar Ice","Solera Kriek","Solera Marzen","Polar Zero","Lácteos San Simón","Quesos Ananké",
                    "Cerveza Tovar","Cerveza Destilo","Ron Roble Viejo","Ron Veroes","Ponche Crema","La Recta","Alimentos Krüger","Charcutería Tovar","Carnes El Tunal",
                    "Pollo Arturo's","Church's Chicken","Wendy's","Burger King","McDonald's","Subway","Pizza Hut","Domino's Pizza","Papa John's","Cinnarolls","Cinnabon",
                    "Araxi Burger","Ávila Burger","Páramo Café","Café Brasil","Café Colonial","Café Anzoátegui","Café Amanecer","Mantequilla Miraflores","Margarina La Fina",
                    "Choco Choco","Choco Break","Chupi Plum","Frunas","Sparkies","Bimbo","Holsum","Pan Ideal","Panaderías La Casona","Pastelería Danubio","Pastelería Mozart",
                    "Helados Cali","Helados La Argentina","La Praline Chocolatier","KKO Real","Chocolates Franceschi","Herklés","Zulka","Azucar","Natilla La Campesina",
                    "Natilla del Llano","Suero Lácteo Paisa","Yogurt Zuli Lac","Migurt","Yogurt Los Andes","Yogurt Táchira","Leche Condensada Natulac",
                    "Dulce de Leche La Colmena","Arequipe Las Tetas","Harina de Trigo Doña María","Aceitunas La Española","Alcaparras Iberia","Mostaza Ketchup",
                    "Mostaza La Giralda","Salsa para Pizza Primor","Salsa Bolognesa Ronco","Salsa Napolitana Capri","Sal La Gema","Sal Marina Refisal","Sal Elefante",
                    "Vinagre El Sol","Vinagre Mavesa","Agua Minalba","Agua Nevada","Zumo","Brasa Burger","Green Martini","Salchichas Arichuna","Mortadela Tapara",
                    "Jamón Endiablado Rica","Jamón Endiablado Fiesta","Galletas Katy","Galletas La Favorita","Chupetas Pin Pop","Caramelos de Leche El Trapiche",
                    "Turrones El Lobo","Panelitas de San Joaquín","Catalinas La Lucha","Palitos de Ajonjolí","Casabe El Pan de la Tierra","Naiboa","Té McCormick",
                    "Manzanilla La Lucha","Gelatinas Royal","Flan Royal","Pudín Royal","Polvo para Hornear Royal","Bicarbonato Arm & Hammer","Levadura Fleishmann",
                    "Esencias McCormick","Vainilla La Lucha","Colorante El Negrito","Sirope de Chocolate Savoy","Sirope de Fresa Savoy", "20/20", "7up", "93", "a-1", "abc",
                    "ace", "act ii", "adams", "add", "agape", "aikas", "ajinomoto", "al-amir", "albro foods", "alcasafoil", "alfa hogar", "alive", "all taste", "allegri", 
                    "alnafol", "alpina", "alumware", "alvarigua", "amanecer", "amesa", "ambrosoli", "amendoim", "anamericana", "andean foods", "andinito", "andre", "anzhen", 
                    "abril", "arcor", "arel", "arepa kseritas", "arizona", "arla", "arm & hammer", "arnold palmer", "aromas del sur", "arquetipo", "arti biscotti", "artesano",
                    "artesano bimbo", "arun", "asolo", "atunmar", "aurora", "aveiro", "avelina", "avila ranch", "baci perugina", "bagsha", "bahia", "bamboo peg", "banquete", 
                    "banu", "barilla", "basso", "bauducco", "bbq", "been", "bell'italia", "bella holandesa", "bellera", "belmont", "belvita", "bene", "benet", "betty crocker", 
                    "bianchi", "bicarbix", "bic", "bienestar organico", "bimbo", "blank&dark", "blanex", "bokas munchy", "bompack", "bon o bon", "bonvivant", "brace", 
                    "brebis dor", "brixia", "bubbaloo", "buen pan", "buenísimo", "bufalinda", "bufito", "burmans", "bustelo", "c.qiaqia", "cacaufoods", "calabuig", "calavita", 
                    "caledonia", "calidex", "california", "camila", "campestre", "camponesa", "canilla", "canoabo", "canta claro", "capri", "caraque", "caribeño coinsa", 
                    "caricias", "carmencita", "carnation", "carré", "casa de miel", "cazorliva", "cega clean", "cemil", "cerelac", "chao", "charmy", "chebell", "cheetos", 
                    "cheese tris", "chichen itza", "chicholac", "chiffon mavesa", "chiquilin", "chocapic", "choco zoo", "chocofit", "chocoton", "chocolate sun", "chocoya", 
                    "choy sun", "chun guang", "chupi chok", "cirio", "cizmeci time", "clabber girl", "clight", "cloihespin", "clorox", "club social", "cocay", "cocosette", 
                    "coffee mate", "coketo", "colavita", "colcafe", "colina", "colombina", "cometin", "condylac", "coposa", "corona", "crismar", "croipan", "crustissimo", 
                    "crystal", "cumbre", "daawat", "dafruta", "daliyuan", "dalvito", "danibisk", "danette", "darnel", "davu", "de cecco", "de la grotta", "de todito", 
                    "del monte", "del bueno", "delicia", "delichips", "delight savoy", "delivey", "della nonna", "delta", "delverde", "di fiore", "diablitos underwood", 
                    "dimare", "dinanda", "divella", "dobon", "docile", "don giuseppe", "don marino", "don paco", "don pedro", "don tito", "don toallin", "doña delia", 
                    "doña eva", "doña flora", "doña maría", "doña tita", "doritos", "downy", "ducale", "ducales", "duketo sun", "dulcemar", "dulces coloridos", "duncan hines", 
                    "duo jia", "eduardo", "el caribeño", "el chichero", "el famoso", "el fogoncito", "el gallo", "el griego bufalinda", "el japonez", "el pastor", "el peñon", 
                    "el rey", "el rey jesus", "el sol", "el taquito", "el titan", "el trapiche", "el tunal", "el turkito", "el viejito", "emana", "equal", "erawan brand", 
                    "eureka", "europa", "eva", "eveba", "evian", "excelencia", "exeline", "expert grill", "extra one", "ey granola", "f.soda", "falidu", "fama de america", 
                    "familia", "fanta", "favorito", "favep", "fcs", "ferrero rocher", "festival", "fiel", "fiesta", "filippo berio", "fit", "five", "flaquito", "fleiscream", 
                    "flips", "flor de abeja", "flor de arauca", "forno bonomi", "franceschi", "freegells", "fresh cup", "frescarini", "frescolita", "freskito santa maria", 
                    "frexco", "frextea", "frica", "fricajita", "frichis", "frito lay", "fritz", "frucfun", "frui fun", "fruit snacks", "fruity pebbles", "fruity snacks", 
                    "frutika", "frutysfit", "fruxi", "full clean", "galak", "galo", "gardenia", "garlin", "garofalo", "gatorade", "gayeton danbisk", "gella montalban", 
                    "gerber", "gloripan", "glup", "glykos", "golden", "granarolo", "granco", "granoro", "granvi lac", "grato", "gravenca", "great grains", "green spot", 
                    "greenstar", "grisbi", "guandy", "guang's", "guilan", "guli", "gullón", "habitus", "haday", "hai long", "haidilao", "haitian", "halls", "halo", 
                    "haoliyuan food", "happy fit", "har", "harinana", "healthy choice", "hefu & chean hao", "heinz", "helios", "heng shun", "hermoza", "hero", "herr's", 
                    "hershey's", "higuera", "hindu", "hit", "hit's", "holsum", "holy krunch", "honey bunches", "hongji haima", "hopla", "househ", "hubba bubba", "huggies", 
                    "hugme", "huj zhu", "hua chang long", "iberia", "ice breakers", "il cantone", "imperial nuts", "inaica", "inaquim", "indian", "indosa", "infus", "intiyan", 
                    "inverni", "iselitas", "isabela", "italdoro", "izypack", "jacks", "jazmin", "jdb", "jif", "jinsiqi", "jinwei", "jinro", "jossie", "juan valdez", "juicefuls", 
                    "jumpi", "justy", "kaito", "kaldini", "kaly", "kampist", "kampist", "katy", "kel", "kelin", "kent", "kettle cooked", "kiero", "kikkoman", "kinder", "king", 
                    "kirkland", "kitkat", "kidsmania", "knorr", "konfit", "kong moon", "konga", "koon mong", "kraft", "kraker slim", "krays", "kron", "ksaksa", "kupiec", 
                    "kwai shu", "la alemana", "la campagnola", "la campesina", "la campiña", "la carabobeña", "la china", "la comadre", "la conquista", "la cumbre", 
                    "la encantada", "la española", "la fauna", "la fragua", "la giralda", "la granja", "la guerita", "la integral", "la lucha", "la mejor", "la molisana", 
                    "la montserratina", "la panamericana", "la parmigiana", "la pastelera", "la pastorena", "la pradera", "la protectora", "la reforma", "la selva", 
                    "la tata de la libertad", "la vaquita azul", "la zulianita", "lactovisoy", "landor", "laoganma", "las delicias de belen", "las llaves", "las marias", 
                    "lassie", "le biscuit", "le olé", "lee kum kee", "lesmi", "lesseur", "lexus", "liangpi paksa", "lifesavers", "lifesystem", "lifetea", "limpia sol", 
                    "lipton", "liri", "llano verde", "lokiño", "lollo", "loreto", "los andes", "los mil y un pan", "los monjes", "los rosales", "lucky strike", "lucya", 
                    "lumalac", "lumé", "m&m's", "macdul sun", "mados", "maggi", "mah", "maite", "maizina americana", "maizoritos", "maltin polar", "manantial", "maracay", 
                    "marbonita", "marcafé", "maribel petrola", "mariachi", "marilu", "marinela", "mariza", "marly", "marques de atares", "maruchan", "mary", "master", 
                    "master foil", "master plast", "master top", "matmac sun", "matrix", "mavesa", "maxcoco", "mazeite", "mccormick", "meco", "mega", "mei fu da", "melindas", 
                    "member's mark", "mengazzoli", "mentitas", "mentos", "meru", "miduchy", "migurt", "mil y un pan", "milka", "millows", "milpa", "minalba", "minda", "mini me", 
                    "mirasol", "misia carmen", "mision mar", "mixtecos", "miya", "monaco", "montaña fresca", "montalban", "monte adentro", "monica", "morita", "mott's", 
                    "mr brown bimbo", "mulino bianco", "multi clean", "munchy", "munchyps", "nabisco", "natuchips", "natural plus", "nature valley", "natures garden", 
                    "naturgourmet", "natulac", "naturoil", "navarro", "nelly", "nerano", "nescafe", "nesquik", "nestle", "nestum", "nevex", "nevada", "newpesca", 
                    "nianrenshi", "nido", "nina", "nissin", "nnova rice", "noel", "nugo", "nunu", "nucita", "nutella", "nutri-express", "nuts", "nuova luna", "oishi", 
                    "oki", "oki oki", "olé", "olimpia", "olympia", "omino bianco", "once once", "onda", "oreo", "orinoquia", "oroweat", "osiris", "osole", "ottima", 
                    "ovomaltina", "p.a.n.", "pafia", "paisa", "pall mall", "palmira", "pampers", "pampero", "pan de tata", "pan ducale", "panamera", "panamei", "panidoce", 
                    "panino", "panpanamericana", "pantanella", "pantera", "panna", "paraguana", "parmalat", "pasion noir", "patagonia", "paveca", "pearl river bridge", "pelli", 
                    "peña negra", "pennsylvania dutch", "pepito", "pepsi", "perugina", "peter", "pillsbury", "pilon", "pinguinos", "piruetas", "pirulin", "piter", "pitbol", "planters", 
                    "plumrose", "polly", "pomi", "popita", "poseidon", "post", "powerade", "powerbar chocofit", "pradera", "predilecta", "prego", "premio", "press", "prestigio", "primor", 
                    "pringles", "proelza", "proteylac", "puig", "punch", "pura nuez", "pure listo", "purex", "purilev", "purisima", "qan ran", "qdol", "quaker", "queseria camila", 
                    "quick blast", "quinoa club", "raquel", "raquety", "raymond foil", "red bull", "red diamond", "rega", "regina", "regional", "renata", "renatto falidu", "renova", "rex", 
                    "rey chef", "rezept", "rica deli", "ricato", "ricolate", "rifel", "rikesa", "riko malt", "ringos munchy", "rio", "rioclaro", "riscossa", "riso inverni", "rita", "ritz", 
                    "robin hood", "robinson crusoe", "robison crusoe", "rockstar", "rodríguez", "roma", "ronco", "rosal", "rossana", "royal", "royal famili", "ruffles", "rupli", "sabena", 
                    "sabroso", "salmas", "salseritos", "saltines", "saludable", "samba", "san domingo", "san michele", "san pellegrino", "san salvador", "san simon", "saneta", "sanissimo", 
                    "sant'anna", "santa madre", "santaniello", "santal", "santiveri", "santoni", "sapito", "sapori", "savini", "savoy", "sazonmix", "schpweppes", "schweppes", "scott", 
                    "secretos de la abuela", "sedita", "seed the sun", "segafredo", "selva", "sensibly natural", "shahe", "shing kee", "shunbaoyoupin", "silsa", "simonetto", "simply 7", 
                    "sindoni", "sirio", "skittles", "sky home", "smac", "snack food", "snickers", "sol", "sonrissa", "sorbeticos", "southern grove", "soyspring", "sparkies", "splenda", 
                    "st. dalfour", "st. moritz", "stadium", "stellina", "suave", "suavitel", "sucream", "sui ma ma", "sun", "sun", "super", "susy", "sutil", "svelty", "sweet bar", 
                    "sweet baby rays", "sweetbrownie", "sweetest", "taf", "taky", "takyta", "tang", "tantan xiang", "tapa amarilla", "tartufi le ife", "taticas", "telisto", "tentazione", 
                    "tertulia", "tevia", "three leaves", "tiburolocos", "tigo", "tigolac", "tigurt", "tip-top", "tip waver", "tiquire flores", "tirma", "tirol", "ti-suf", "tk", "toblerone", 
                    "toddy", "tom", "tomatodo", "torondoy", "toronto", "tortillas agave", "tortilleria los gonzales", "tosh", "tostitos", "trento", "trident", "trident", "trolli", "trululu", 
                    "truvia", "tubis wynco", "tunal", "turrones el lobo", "tuscan garden", "tuto mate", "twinkies", "twisti keso", "twix", "umiz", "underwood", "unico", "upaca", "vale", 
                    "valle canoabo", "valle fresh", "valp", "vanilla bake", "vanish", "vatel", "vel", "venela", "venepan", "venfood", "vero pan", "v7", "vicone", "vidactiva", "vilay", 
                    "villa láctea", "visciano", "visiclass", "vittale branza", "viva", "vivo", "volcán", "wacky shark", "wangzai r", "weiyicun", "welch's", "wepa", "white rabbit", "willinger", 
                    "wilos", "win", "wipala", "wonderful", "wom biters", "wrigleys", "wynco", "wynwoond", "xiotel", "xoxo", "xue li ci", "xu ji", "ye xiang", "yesheng", "yill", "yinjiang", 
                    "yoffi", "yoka", "yolo", "yoy foods", "yog pro", "yogulito", "yong ling", "yujing", "yukery", "yuky-pak", "yumart", "yune", "yzeco", "zanetti", "zhangxicun", "zhen xian da", 
                    "zhong shan", "ziploc", "zulia", "zupla"]

STOP_WORDS = {'whisky', 'ron', 'cerveza', 'botella', 'a', 'de', 'la', 'el', 'en', 'con', 'para', 'p/r', 'p/c', 'y', 'o', 'lata', 'bolsa', 'paquete'}