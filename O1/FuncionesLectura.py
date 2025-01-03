import os
import re
import pandas as pd
from langdetect import detect

def procesarOracion(bloque):
    """
        Function created by Harvy Martínez (@xnehil)
    """
    #Quitar espacios en blanco
    bloque = bloque.strip()
    return bloque

def leerTxt(ruta="../textos", data={}):
    """
        Function created by Harvy Martínez (@xnehil)
    """
    primera = True
    id = locutor = transcripcion =  palabras = traduccionLibre = traduccionPalabra = morfologia = pos =""


    for filename in os.listdir(ruta):
        #Si el archivo es un .txt
        if filename.endswith('.txt'):
            #Se abre el archivo
            #Saltar el archivo 'textos/DICCIONARIOISKONAWA7.txt' porque no es un archivo de texto
            if filename == 'DICCIONARIOISKONAWA7.txt':
                continue
            with open(ruta+'/'+filename, encoding='utf-8') as file:
                #Se lee el archivo
                transcripcion = file.read()
                #Por cada linea en el archivo
                for line in transcripcion.split('\n'):
                    #Skip si la linea es solo espacios en blanco o saltos de linea
                    if not line.strip():
                        continue
                    tipo_match = re.search(r'^\\\S*', line)
                    if tipo_match:
                        tipo = tipo_match.group()
                        # Remove the tipo from the line to get the oracion
                        oracion = re.sub(r'^\\\S* ', '', line)
                        #Quitar espacios en blnaco
                        oracion = oracion.strip()
                        
                        # Process the oracion based on the tipo
                        if tipo == '\\ref':
                            id = oracion
                            # Append the previous data before resetting variables
                            if not primera:
                                key = f"{filename}_{id}"
                                data[key] = {
                                    'id': id, 
                                    'speaker': locutor, 
                                    'transcription': transcripcion, 
                                    'text': palabras.strip(), 
                                    'gloss_es': traduccionPalabra.strip(),
                                    'free_translation': traduccionLibre,
                                    'morpheme_break': morfologia.strip(),
                                    'pos': pos.strip(),
                                    'file': filename
                                }
                            primera = False
                            # Reset the variables
                            locutor = transcripcion = palabras = traduccionLibre = traduccionPalabra = morfologia = pos = ""
                        elif tipo == '\\ELANParticipant':
                            locutor = oracion
                        elif tipo == '\\trs':
                            transcripcion = procesarOracion(oracion)
                        elif tipo == '\\tx':
                            palabras += procesarOracion(oracion) + ' '
                        elif tipo == '\\gn':
                            traduccionPalabra += oracion + ' '
                        elif tipo == '\\ft':
                            traduccionLibre = procesarOracion(oracion) 
                        elif tipo == '\\mb':
                            morfologia += oracion + ' '
                        elif tipo == '\\ps':
                            pos += oracion + ' '
                        else:
                            continue
                primera = True
    if not primera:
        key = f"{filename}_{id}"
        data[key] = {
            'id': id, 
            'speaker': locutor,
            'transcription': transcripcion,
            'text': palabras.strip(),
            'gloss_es': traduccionPalabra.strip(),
            'free_translation': traduccionLibre,
            'morpheme_break': morfologia.strip(),
            'pos': pos.strip(),
            'file': filename
        }

def leerEaf(ruta="../textos", data={}):
    """
        Function created by Harvy Martínez (@xnehil)
    """
    #Solo se leen los archivos que no han sido procesados como .txt
    archivos = []
    for filename in os.listdir(ruta):
        if filename.endswith('.eaf'):
            if not os.path.exists(ruta+'/'+filename[:-4]+'.txt'):
                archivos.append(filename)

    for filename in archivos:
        locutor = texto = palabras = traduccionLibre= traduccionPalabra = morfologia = pos = id = None
        dentro_tier = False
        with open(ruta+'/'+filename, encoding='utf-8') as file:
            texto = file.read()
            annotation_id = None
            #Cada archivo eaf es un xml. Nos interesa el valor de los atributos 'ANNOTATION_VALUE' de los elementos 'TIER' que tengan el atributo 'TIER_ID' igual a 'trsx@algo'
            #Por cada linea en el archivo
            for line in texto.split('\n'):
                #Skip si la linea es solo espacios en blanco o saltos de linea
                if not line.strip():
                    continue
                #Buscar fin de tier
                end_tier_match = re.search(r'</TIER>', line)
                # Search for the self-closing tier pattern
                self_closing_tier_match = re.search(r'<TIER\s+.*?/>', line)

                # Check if either pattern is found
                if end_tier_match or self_closing_tier_match:
                    dentro_tier = False
                    # If it's a self-closing tier, ignore the line
                    if self_closing_tier_match:
                        continue

                if dentro_tier:
                    if tier_id.startswith('trs@'):
                        #Transcripción original
                        alignable_annotation_match = re.search(r'<ALIGNABLE_ANNOTATION[^>]*ANNOTATION_ID="([^"]+)"', line)
                        if alignable_annotation_match:
                                annotation_id = alignable_annotation_match.group(1)
                                id = annotation_id
                        if id is not None:
                            annotation_value_match = re.search(r'<ANNOTATION_VALUE>([^<]+)</ANNOTATION_VALUE>', line)
                            if annotation_value_match:
                                transcripcion = procesarOracion(annotation_value_match.group(1))
                                key = f"{filename}_{id}"
                                data[key] = {
                                    'id': id, 
                                    'speaker': locutor, 
                                    'transcription': transcripcion, 
                                    'text': palabras, 
                                    'gloss_es': traduccionPalabra,
                                    'free_translation': traduccionLibre,
                                    'morpheme_break': morfologia,
                                    'pos': pos,
                                    'file': filename
                                }
                                annotation_id = None

                    elif tier_id.startswith('tx@'):
                        ref_annotation_match = re.search(r'<REF_ANNOTATION[^>]*ANNOTATION_ID="([^"]+)" ANNOTATION_REF="([^"]+)"', line)
                        # print("Buscando referencia a anotación en tier tx")
                        if ref_annotation_match:
                            # print ("Se encontró una referencia a una anotación con valor {} y referencia {}".format(ref_annotation_match.group(1), ref_annotation_match.group(2)))
                            annotation_id = ref_annotation_match.group(1)
                            #Buscar en data el elemento con el id igual a annotation_ref y archivo igual a filename
                            annotation_ref = ref_annotation_match.group(2)
                            key = f"{filename}_{annotation_ref}"
                            # print(key)
                        if annotation_id is not None:
                            annotation_value_match = re.search(r'<ANNOTATION_VALUE>([^<]+)</ANNOTATION_VALUE>', line)
                            if annotation_value_match:
                                annotation_id = None
                                palabras = annotation_value_match.group(1)
                                data[key]['text'] = palabras
                                # print(key)
                                annotation_id = None
                                
                    elif tier_id.startswith('ft@'):
                        #Cosa de traducción
                        ref_annotation_match = re.search(r'<REF_ANNOTATION[^>]*ANNOTATION_ID="([^"]+)" ANNOTATION_REF="([^"]+)"', line)
                        if ref_annotation_match:
                            annotation_id = ref_annotation_match.group(1)
                            #Buscar en data el elemento con el id igual a annotation_ref y archivo igual a filename
                            annotation_ref = ref_annotation_match.group(2)
                            key = f"{filename}_{annotation_ref}"
                            # print(key)
                        if annotation_id is not None:
                            annotation_value_match = re.search(r'<ANNOTATION_VALUE>([^<]+)</ANNOTATION_VALUE>', line)
                            if annotation_value_match:
                                traduccion = annotation_value_match.group(1)
                                # print(key)
                                data[key]['free_translation'] = traduccion
                                
                else:
                    #Buscamos primero un elemento 'TIER' que tenga el atributo 'TIER_ID' igual a 'trs@algo'
                    tier_match = re.search(r'<TIER[^>]*PARTICIPANT="([^"]+)"[^>]*TIER_ID="([^"]+)"', line)
                    if tier_match:
                        locutor = tier_match.group(1)
                        tier_id = tier_match.group(2)
                        # print("Entrando en tier {} con locutor {} en archivo {}".format(tier_id, locutor, filename))
                        dentro_tier = True


def clean_text(text):
    """
        Function created by Amy Trujillo (@amyyy09)
    """
    return re.sub(r'\(\d\)', '', text).strip()

def parse_txt(file):
    """
        Function created by Amy Trujillo (@amyyy09)
    """
    data = []
    with open(file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    current_entry = {}
    current_tag = None
    current_value = []

    for line in lines:
        line = line.strip()
        if line.startswith('\\lx'):
            if current_entry:
                if current_tag:
                    current_entry[current_tag] = ' '.join(current_value).strip()
                data.append(current_entry)
            current_entry = {'lex_isc': clean_text(line.strip('\\lx').strip())}
            current_tag = None
            current_value = []
        elif line.startswith('\\lc'):
            current_entry['lex_citation'] = clean_text(line.strip('\\lc').strip())
            current_tag = None
            current_value = []
        elif line.startswith('\\ps'):
            current_entry['pos'] = line.strip('\\ps').strip()
            current_tag = None
        elif line.startswith('\\gn') and 'gloss_es' not in current_entry:
            if current_tag:
                current_entry[current_tag] = ' '.join(current_value).strip()
            current_tag = 'gloss_es'
            current_value = [line.strip('\\gn').strip()]
        elif line.startswith('\\rn') and 'gloss_es' not in current_entry:
            if current_tag:
                current_entry[current_tag] = ' '.join(current_value).strip()
            current_tag = 'gloss_es'
            current_value = [line.strip('\\rn').strip()]
        elif line.startswith('\\dn') and 'def_es' not in current_entry:
            if current_tag:
                current_entry[current_tag] = ' '.join(current_value).strip()
            current_tag = 'def_es'
            current_value = [line.strip('\\dn').strip()]
        elif line.startswith('\\'):
            if current_tag:
                current_entry[current_tag] = ' '.join(current_value).strip()
            current_tag = None
        else:
            if current_tag:
                current_value.append(line)

    if current_entry:
        if current_tag:
            current_entry[current_tag] = ' '.join(current_value).strip()
        data.append(current_entry)
    
    df = pd.DataFrame(data, columns=['lex_isc', 'lex_citation', 'pos', 'gloss_es', 'def_es'])
    return df



def is_spanish(text):
    """
        Function created by Harvy Martínez (@xnehil)
    """
    try:
        return detect(text) == 'es'
    except:
        return False
    
def leerCorpus(ruta="../textos", limpiar=True):
    """
        Function created by Harvy Martínez (@xnehil)
    """
    data = {}
    leerTxt(ruta=ruta, data=data)
    leerEaf(ruta=ruta, data=data)
    df = pd.DataFrame(data).transpose().reset_index(drop=True)
    #Limpiar 
    if limpiar:
        print(f"Antes de limpiar: {df.shape}")
        df = df[~df['transcription'].apply(is_spanish)]
        print(f"Después de limpiar: {df.shape}")
        df = df[df['transcription'].str.strip() != '']
        
    #Cualquier campo vacío o cadena vacía debe ser null
    df = df.replace('', None)
    df = df.replace('\\mb', None)
    #Eliminar filas con None en id, speaker, transcription, free_translation, file
    df = df.dropna(subset=['id', 'speaker', 'transcription', 'free_translation', 'file'])
    print(f"Después de limpiar: {df.shape}")
    #Id debe ser file sin la extensión seguido de un guión y el id
    df['id'] = df['file'].str.replace('.txt' or '.eaf', '', regex=False) + '_' + df['id'].astype(str)

    df = df[['id', 'speaker', 'transcription', 'text', 'morpheme_break', 'pos', 'gloss_es', 'free_translation', 'file']]

    # Estándarizar las etiquetas POS
    df = standardize_pos_tag(df)

    df_monolingual = df[['id', 'speaker', 'transcription', 'morpheme_break', 'pos', 'file']]

    df_bilingual = get_bilingual(df)

    return df_monolingual, df_bilingual

def get_bilingual(df):
    """
        Function created by amy Trujillo (@amyyy09)
    """
    
    # Eliminar duplicados de transcription y gloss_es
    df = df.drop_duplicates(subset=['transcription', 'gloss_es'])

    # Eliminar columna speaker
    df = df.drop(columns=['speaker', 'text'])

    return df

def standardize_pos_tag(df):
    """
        Function created by Amy Trujillo (@amyyy09)
    """
    # Drop rows that have 'ps' in the pos column
    df = df[~df['pos'].str.contains(r'\bps\b', na=False)]

    # Define replacements
    replacements = {
        'sufv.intr': 'suf. v.intr',
        'advv.intr': 'adv. v.intr',
        'advv': 'adv. v',
        'demadv': 'dem. adv',
        'conec': 'conect',
        'ide': 'ideo',
        'int.v.tran': 'intj. v.tran',
        'ono': 'onom',
        'pre': 'prep',
        'v.amb': 'v.ambi',
        'v.int': 'v.intr',
        'v.tran': 'v.tr',
        'clitn': 'clit n',
        'clitdem': 'clit dem',
        'clitpart': 'clit part',
        'clitv': 'clit v',
        'int': 'intj',
        'interj': 'intj',
        'inter': 'intj',
        'prom': 'pal.int',
        'pal.intj': 'pal.int'
    }

    # Replace patterns in the pos column with exact word boundaries
    for old, new in replacements.items():
        df.loc[:, 'pos'] = df['pos'].str.replace(re.escape(old) + r'\b', new, regex=True)

    # Remove semicolons
    df.loc[:, 'pos'] = df['pos'].str.replace(';', '', regex=False)

    # Replace any comma with a period
    df.loc[:, 'pos'] = df['pos'].str.replace(',', '.', regex=False)

    # Add a period after a letter that is followed by a space or the end of the line
    df.loc[:, 'pos'] = df['pos'].str.replace(r'(?<=[a-zA-Z])(?=\s|$)', '.', regex=True)

    return df