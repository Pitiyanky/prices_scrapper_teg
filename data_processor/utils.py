import nltk
from nltk.corpus import cess_esp
from nltk.tag import UnigramTagger, BigramTagger, TrigramTagger
import re
import pandas as pd

cess_tagged_sents = cess_esp.tagged_sents()
tagger = TrigramTagger(
    train=cess_tagged_sents,
    backoff=BigramTagger(
        train=cess_tagged_sents,
        backoff=UnigramTagger(
            train=cess_tagged_sents,
            backoff=nltk.DefaultTagger('NC')
        )
    )
)

def tokenize_spanish_desc(desc):
    """Tokenización especial para descripciones con abreviaturas"""
    tokens = []
    desc = desc.lower().replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
    for part in re.split(r'[\s./]+', desc):
        if part and not part.isdigit() and not re.match(r'^\d+[a-z]*$', part):
            tokens.append(part)
    return tokens

def get_product_type(desc):
    tokens = tokenize_spanish_desc(desc)
    if not tokens:
        return ""
    
    tagged = tagger.tag(tokens)
    
    unidades = {'gr', 'kg', 'lt', 'ml', 'g', 'und', 'u', 'hj', 'h', 'rll', 'r', 's', 'cc', 'x', 'xl'}
    preposiciones = {'de', 'con', 'para', 'y'}
    
    phrase_tokens = []
    last_was_noun = False
    last_was_prep = False
    
    for word, tag in tagged:
        word_lower = word.lower()
        
        if word_lower in unidades or re.match(r'^\d+[a-z]*$', word_lower):
            break
        
        is_noun = tag and tag.startswith('NC')
        is_adj = tag and tag.startswith('AQ')
        is_prep = word_lower in preposiciones
        
        if is_noun or is_adj:
            if last_was_prep:
                phrase_tokens.append(word)
                last_was_noun = True
                last_was_prep = False
            elif not phrase_tokens:
                phrase_tokens.append(word)
                last_was_noun = True
            elif last_was_noun and is_adj:
                phrase_tokens.append(word)
                last_was_noun = False
            else:
                break
        elif is_prep and phrase_tokens:
            if last_was_noun:
                phrase_tokens.append(word)
                last_was_prep = True
                last_was_noun = False
            else:
                break
        else:
            if phrase_tokens:
                break

    if phrase_tokens and len(phrase_tokens) > 1 and phrase_tokens[-1].lower() in preposiciones:
        phrase_tokens.pop()
        
    return " ".join(phrase_tokens)

class UDMExtractor:
    def __init__(self):
        self.unit_priority_list = self._build_unit_priority_list()
        self.all_unit_variants = set()
        for _, variants in self.unit_priority_list:
            self.all_unit_variants.update(variants)
        
    def _build_unit_priority_list(self):
        return [
            ("unidades", ["un", "und", "unds", "uni", "unid", "unids", "unidad", "unidades", 
                    "u", "p", "pz", "pza", "pzas", "sobre", "sobres", "s", "paq", "paquetes"]),

            ("gramos", ["g", "gr", "grs", "gramos", "gramo", "gs"]),
            ("kilogramos", ["kg", "kilos", "kilo", "k"]),
            
            ("mililitros", ["ml", "cc"]),
            ("litros", ["l", "lt", "lts", "litros", "litro"]),
            
            ("rollos", ["r", "rollo", "rollos", "rll", "rlls"]),
            ("hojas", ["h", "hj", "hoja", "hojas"]),
            
            ("onzas", ["oz", "onz"]),
            ("libras", ["lb", "lbs", "libra", "libras"]),
            ("bolsas", ["bol", "bolsa", "bolsas"]),
            ("galones", ["gal"]),
            ("centimetros", ["cm"]),
            ("metros", ["m", "mts", "metro", "metros"]),
            ("xl", ["xl", "extra grande", "extra-large"]),
        ]
    
    def _tokenize_product_name(self, name):
        tokens = []
        for part in re.split(r'[\s./-]+', name):
            if part and not part.isdigit() and not re.match(r'^\d+[a-z]*$', part):
                tokens.append(part)
        return tokens
    
    def _is_count_unit(self, unit):
        """Determina si la unidad es de conteo (puede ser implícita)"""
        unit_lower = unit.lower()
        for normalized, variants in self.unit_priority_list:
            if normalized == "unidades" and unit_lower in variants:
                return True
        return False
    
    def _extract_quantity_unit_pair(self, name):

        numeric_pattern = r'(\d+[\.,]?\d*)\s*([a-zA-Z]{1,5})\b'
        match = re.search(numeric_pattern, name)
        if match:
            quantity_str = match.group(1).replace(',', '.')
            unit_raw = match.group(2).lower()
            try:
                quantity = float(quantity_str)
                if unit_raw in self.all_unit_variants:
                    return quantity, unit_raw
            except ValueError:
                pass
        
        tokens = self._tokenize_product_name(name)
        if not tokens:
            return None, None
        
        tagged = tagger.tag(tokens)
        
        for i, (word, tag) in enumerate(tagged):
            if tag == 'Z':  # Número
                quantity_str = word.replace(',', '.')
                
                if i + 1 < len(tagged):
                    next_word, next_tag = tagged[i+1]
                    if next_word.lower() in self.all_unit_variants:
                        try:
                            quantity = float(quantity_str)
                            return quantity, next_word.lower()
                        except ValueError:
                            pass
        
        for i in range(len(tagged)-1, -1, -1):
            word, tag = tagged[i]
            word_lower = word.lower()
            
            if (word_lower in self.all_unit_variants and
                len(word) <= 5):
                for j in range(max(0, i-3), i):
                    prev_word, prev_tag = tagged[j]
                    if prev_tag == 'Z':
                        try:
                            quantity = float(prev_word.replace(',', '.'))
                            return quantity, word_lower
                        except ValueError:
                            pass
            for i, (word, tag) in enumerate(tagged):
                word_lower = word.lower()
                if self._is_count_unit(word_lower):
                    return 1, word_lower
        
        return 1, 'unidades'

    def _normalize_unit(self, unit_raw):
        """Normaliza unidades usando lista priorizada"""
        if unit_raw is None:
            return None
        
        unit_lower = unit_raw.lower()
        
        for normalized_unit, variants in self.unit_priority_list:
            if unit_lower in variants:
                return normalized_unit
        
        return unit_raw
    
    def extract_and_normalize_udm(self, product_name_series):
        """Procesa una serie de nombres de producto"""
        if not isinstance(product_name_series, pd.Series):
            product_name_series = pd.Series(product_name_series)
        
        results = []
        for name in product_name_series:
            quantity, unit_raw = self._extract_quantity_unit_pair(name)
            normalized_unit = self._normalize_unit(unit_raw)
            results.append({
                'extracted_quantity': quantity,
                'unit_raw': unit_raw,
                'normalized_unit': normalized_unit
            })
        
        return pd.DataFrame(results)