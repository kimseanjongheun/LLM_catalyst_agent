import sys
import json
import re
import numpy as np
import matplotlib
import pylab as p
from ase.db import connect
from ase.visualize import view
import matplotlib.transforms
import requests

# from tools import ordered_metals, get_AB_from_formula, references, site2int, site_labels
import pandas as pd


"""
Adsorbates includes: H, N, C, O, S, CH, NH, CH2, CH3, OH and H2O

sites can be:
'~', '~hollow', '~bridge, '~top', hollow|A_A_A|HCP, hollow|A_A_A|FCC, hollow|A_A_B|HCP, hollow|A_A_B|FCC,
bridge|A_A|A, bridge|A_A|B, bridge|A_B|A, bridge|B_B|B, top|A, top|B
Also you will have to specift the Structure Bericht symbol (SB_symbol) of the alloy, which can be L12 or L10

"""

import pandas as pd
import numpy as np

import pandas as pd
import numpy as np



# from cathub.query import get_reactions
def execute_graphQL(query_string, table=None):
    root = 'http://api.catalysis-hub.org/graphql'
    print('Connecting to database at {root}'.format(root=root))
    print('')
    print('Executing query:')
    print('')
    print(query_string)
    print('')
    print('Getting data from server...')
    print('')
    data = requests.post(root, {'query': query_string})
    try:
        data = data.json()['data']
        print('Data fetched!')
    except BaseException:
        print(data)

    if not table == 'logs':
        # Load nested dictionaries
        for i, node in enumerate(data['reactions']['edges']):
            node = node['node']
            for key, value in list(node.items()):
                try:
                    value_dict = json.loads(value)
                    node[key] = value_dict
                except (ValueError, TypeError):
                    pass

    return data

def graphql_query(table='reactions',
                  subtables=[],
                  columns=['chemicalComposition',
                           'reactants',
                           'products'],
                  n_results=10,
                  queries={}):

    statement = '{'
    statement += '{}('.format(table)
    if not table == 'logs':
        if n_results != 'all':
            statement += 'first: {}'.format(n_results)
    for key, value in queries.items():
        if isinstance(value, str):
            if table == 'logs':
                statement += '{}: "{}"'.format(key, value)
            else:
                statement += ', {}: "{}"'.format(key, value)
        elif isinstance(value, bool):
            if value:
                statement += ', {}: true'.format(key)
            else:
                statement += ', {}: false'.format(key)
        else:
            statement += ', {}: {}'.format(key, value)

    statement += ') {\n'
    if table == 'logs':
        statement += ' edges {\n    node { \n'
    else:
        statement += ' totalCount\n  edges {\n    node { \n'
    for column in columns:
        column = map_column_names(column)
        statement += '      {}\n'.format(column)
    for subtable in subtables:
        statement += '      {}'.format(subtable)
        statement += '{\n'
        for column in all_columns[subtable]:
            statement += '        {}\n'.format(column)
        statement += '      }\n'
    statement += '    }\n'
    statement += '  }\n'
    statement += '}}'

    return statement

def query(table='reactions',
          columns=['chemicalComposition',
                   'reactants',
                   'products'],
          subtables=[],
          n_results=10,
          queries={},
          print_output=False):

    if table == 'logs':
        query_string = graphql_query(table=table,
                                     columns=columns,
                                     queries=queries)
    else:
        query_string = graphql_query(table=table,
                                     subtables=subtables,
                                     columns=columns,
                                     n_results=n_results,
                                     queries=queries)

    return execute_graphQL(query_string, table=table)

def map_column_names(column):
    mapping = {'surface': 'chemicalComposition'}

    if column in mapping:
        return mapping[column]
    else:
        return column

def get_reactions(columns='all', n_results=20, write_db=False, **kwargs):
    """
    Get reactions from server

    Give key value strings as arguments
    """
    if write_db or columns == 'all':
        columns = all_columns['reactions']
    queries = {}
    for key, value in kwargs.items():
        key = map_column_names(key)
        if key == 'distinct':
            if value in [True, 'True', 'true']:
                queries.update({key: True})
                continue
        if isinstance(value, int) or isinstance(value, float):
            queries.update({key: value})
        else:
            queries.update({key: '{0}'.format(value)})

    subtables = []
    if write_db:
        subtables = ['reactionSystems', 'publication']
    else:
        subtables = []
    data = query(table='reactions', subtables=subtables,
                 columns=columns,
                 n_results=n_results, queries=queries)

    if not write_db:
        return data

    print('Writing result to Reactions.db')
    unique_ids = []
    for row in data['reactions']['edges']:
        with CathubSQLite('Reactions.db') as db:
            row = row['node']
            key_values = {}
            for key in all_columns['reactions']:
                v = row[key]
                # if isinstance(v, unicode):
                #    v = v.encode('utf-8')
                try:
                    v = json.loads(v)
                except BaseException:
                    pass
                key_values[convert(key)] = v
            ase_ids = {}
            energy_corrections = {}

            for row_rs in row['reactionSystems']:
                if row_rs['name'] == 'N/A':
                    continue
                ase_ids[row_rs['name']] = row_rs['aseId']
                energy_corrections[row_rs['name']] = row_rs['energyCorrection']

            if not ase_ids:
                ase_ids = None
                energy_corrections = None
            else:
                unique_ids += ase_ids.values()
            key_values['ase_ids'] = ase_ids
            key_values['energy_corrections'] = ase_ids

            # publications
            pub_key_values = {}
            row_p = row['publication']
            for key in all_columns['publications']:
                pub_key_values[convert(key)] = row_p[key]
            db.write_publication(pub_key_values)

            # reactions and reaction_systems
            id = db.check(key_values['chemical_composition'],
                          key_values['reaction_energy'])
            if id is None:
                id = db.write(key_values)
            else:
                db.update(id, key_values)

    if ase_ids is not None:
        # Ase structures
        with ase.db.connect('Reactions.db') as ase_db:
            con = ase_db.connection
            cur = con.cursor()
            cur.execute('SELECT unique_id from systems;')
            unique_ids0 = cur.fetchall()
            unique_ids0 = [un[0] for un in unique_ids0]
            unique_ids = [un for un in unique_ids if un not in unique_ids0]
            for unique_id in list(set(unique_ids)):
                # if ase_db.count('unique_id={}'.format(unique_id)) == 0:
                atomsrow = get_atomsrow_by_id(unique_id)
                ase_db.write(atomsrow)

    print('Writing complete!')

    return data


def site2int(site):
    """
    사이트 정보를 정수로 변환
    
    Examples:
    - 'bridge|A_A|B' -> 2
    - 'top|A' -> 1
    - 'hollow|A_A_A|HCP' -> 3
    - '~' -> 0
    """
    site_mapping = {
        'top': 1,
        'bridge': 2, 
        'hollow': 3,
        'fcc': 4,
        'hcp': 5,
        '~': 0
    }
    
    site_lower = site.lower()
    
    # 정확한 매칭 먼저 확인
    if site_lower in site_mapping:
        return site_mapping[site_lower]
    
    # 부분 매칭으로 사이트 타입 찾기
    for key, value in site_mapping.items():
        if key in site_lower:
            return value
    
    # 기본값
    return 0

def get_AB_from_formula(formula: str):
    """
    화학식에서 원소 기호와 조성을 추출하여 반환한다.
    - 예: "Au3Ag" -> ('Au', 'Ag', 3, 1, None)
    - 예: "Ag"    -> ('Ag', None, 1, None, None)

    Args:
        formula (str): 화학식 (예: "Au3Ag", "Ag")

    Returns:
        tuple: (A, B, composition_A, composition_B, SB_symbol)
    """
    # 화학식에서 [원소][숫자옵션] 패턴 추출
    parts = re.findall(r'[A-Z][a-z]?\d*', formula)

    if not parts:
        raise ValueError(f"화학식 '{formula}'에서 원소를 찾을 수 없습니다.")

    # 원소와 계수 분리
    elements = []
    compositions = []
    for p in parts:
        elem = re.match(r'([A-Z][a-z]?)', p).group(1)
        num_match = re.search(r'\d+', p)
        num = int(num_match.group()) if num_match else 1  # 숫자 없으면 1
        elements.append(elem)
        compositions.append(num)

    # 최소 한 원소 존재
    A = elements[0]
    composition_A = compositions[0]

    if len(elements) > 1:
        B = elements[1]
        composition_B = compositions[1]
    else:
        B = None
        composition_B = None


    return A, B, composition_A, composition_B


def analyze_adsorption(adsorbate):

    ordered_metals = ['Ag', 'Au', 'Cd', 'Co', 'Cr', 'Cu', 'Fe',
     'Hf', 'Hg', 'Ir', 'La', 'Mn', 'Mo', 'Nb', 'Ni',
      'Os', 'Pd', 'Pt', 'Re', 'Rh', 'Ru', 'Sc', 'Ta',
       'Tc', 'Ti', 'V', 'W', 'Y', 'Zn', 'Zr'
    ]
    
    metalstrx = ['\n{}'.format(o) if i in range(0,37,2) else o for i, o in enumerate(ordered_metals)]
    metalstry = ['     {}'.format(o) if i in range(1,37,2) else o for i, o in enumerate(ordered_metals)]
    dim = len(ordered_metals)
    adsorption_site = '~'
    SB_symbol = 'L12'  # 'L10' or 'L12'

    data = get_reactions(n_results='all',
                         pubId='MamunHighT2019',
                         sites=adsorption_site,
                         products=adsorbate,
                         columns=['surfaceComposition, reactionEnergy', 'sites', 'products'])

    data = data['reactions']
    totalCount = data['totalCount']
    edges = data['edges']
    site_points = (np.array(range(1, 14)) - 0.5) * 20 / 12

    # Define dim based on the length of ordered_metals
    dim = len(ordered_metals)
    EADS = np.zeros([dim, dim])
    SITES = np.zeros([dim, dim])
    EADS.fill(None)
    SITES.fill(None)

    # Initialize lists to store the data
    metal1_list = []
    metal1_composition_list = []
    metal2_list = []
    metal2_composition_list = []
    ads_energy_list = []
    site_list = []
    for edge in edges:
        result = edge['node']

        adsorbates = list(result['products'].keys())
        prefactor_adsorbate = list(result['products'].values())[0]

        # Only include results with one adsorbate
        if len(adsorbates) > 1 or prefactor_adsorbate > 1:
            continue

        formula = result['surfaceComposition']
        E = result['reactionEnergy']
        sites = result['sites']

        site = list(sites.values())[0]
        if 'tilt' in site:
            continue
        
        site = site2int(site)

        A, B, composition_A, composition_B = get_AB_from_formula(formula)

        if A not in ordered_metals or B not in ordered_metals:
            continue

        iA = ordered_metals.index(A)
        iB = ordered_metals.index(B)

        # Remove '\n' from metal names
        metal1 = metalstrx[iA].strip()
        metal2 = metalstrx[iB].strip()
        # Append data to lists
        metal1_list.append(metal1)
        metal2_list.append(metal2)
        metal1_composition_list.append(composition_A / (composition_A + composition_B))
        metal2_composition_list.append(composition_B / (composition_A + composition_B))
        site_list.append(site)
        ads_energy_list.append(E)

        if np.isnan(EADS[iA, iB]) or EADS[iA, iB] > float(E):
            EADS[iA, iB] = E
            SITES[iA, iB] = site
            if SB_symbol == 'L10':
                EADS[iB, iA] = E
                SITES[iB, iA] = site

    # Create a pandas DataFrame
    data_her = {
        'Metal1': metal1_list,
        'Metal2': metal2_list,
        'Metal1_Composition': metal1_composition_list,
        'Metal2_Composition': metal2_composition_list,
        'Site': site_list,
        'ads_energy': ads_energy_list
    }

    df = pd.DataFrame(data_her)
    return df, EADS



ordered_metals = ['Ag', 'Au', 'Cu', 'Fe', 'Ni', 'Pd', 'Pt', 'Rh', 'Ru', 'Sc', 'Ti', 'V', 'W', 'Y', 'Zr']
metalstrx = ['\n{}'.format(o) if i in range(0,37,2) else o for i, o in enumerate(ordered_metals)]
metalstry = ['     {}'.format(o) if i in range(1,37,2) else o for i, o in enumerate(ordered_metals)]
dim = len(ordered_metals)
adsorption_site = '~'
SB_symbol = 'L12'  # 'L10' or 'L12'

# Example usage:
adsorbate = 'H'
result_df, EADS = analyze_adsorption(adsorbate)
print(result_df.head())
print(result_df.shape)

output_path = fr"C:\Users\spark\Desktop\LLM_Catalyst_Agent\data\MamunHighT2019\adsorption_data_{adsorbate}_{SB_symbol}.csv"
result_df.to_csv(output_path, index=False)
print(f"Data saved to {output_path}")
