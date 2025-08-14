import ase
from ase.io import read, write
import requests, sys, os, json, io, pickle, json, pickle
from ase.optimize import LBFGS
from fairchem.core import pretrained_mlip, FAIRChemCalculator
from ase.calculators.emt import EMT
import copy
import numpy as np
import matplotlib.pyplot as plt
import tqdm

GRAPHQL = 'http://api.catalysis-hub.org/graphql'
def fetch(query):
    return requests.get(
        GRAPHQL, {'query': query}
    ).json()['data']

def reactions_from_dataset(pub_id, page_size=10, max_count=None):
    reactions = []
    has_next_page = True
    start_cursor = ''
    page = 0
    while has_next_page:
        data = fetch("""{{
      reactions(pubId: "{pub_id}", first: {page_size}, after: "{start_cursor}") {{
        totalCount
        pageInfo {{
          hasNextPage
          hasPreviousPage
          startCursor
          endCursor 
        }}  
        edges {{
          node {{
            Equation
            reactants
            products
            reactionEnergy
            reactionSystems {{
              name
              systems {{
                energy
                InputFile(format: "json")
              }}
            }}  
          }}  
        }}  
      }}    
    }}""".format(start_cursor=start_cursor,
                 page_size=page_size,
                 pub_id=pub_id,
                ))
        has_next_page = data['reactions']['pageInfo']['hasNextPage']
        start_cursor = data['reactions']['pageInfo']['endCursor']
        page += 1
        print(has_next_page, start_cursor, page_size * page, data['reactions']['totalCount'])
        reactions.extend(map(lambda x: x['node'], data['reactions']['edges']))

        # ✅ 원하는 개수만큼 도달하면 중단
        if max_count and len(reactions) >= max_count:
            reactions = reactions[:max_count]
            break

    return reactions


def aseify_reactions(reactions):
    for i, reaction in enumerate(reactions):
        for j, _ in enumerate(reactions[i]['reactionSystems']):
            with io.StringIO() as tmp_file:
                system = reactions[i]['reactionSystems'][j].pop('systems')
                tmp_file.write(system.pop('InputFile'))
                tmp_file.seek(0)
                atoms = ase.io.read(tmp_file, format='json')
            calculator = ase.calculators.singlepoint.SinglePointCalculator(
                atoms,
                energy=system.pop('energy')
            )
            atoms.set_calculator(calculator)
            #print(atoms.get_potential_energy())
            reactions[i]['reactionSystems'][j]['atoms'] = atoms
        # flatten list further into {name: atoms, ...} dictionary
        reactions[i]['reactionSystems'] = {x['name']: x['atoms']
                                          for x in reactions[i]['reactionSystems']}
def correct_stoi(name,stoi):
    if ("star" in name) and (stoi > 1):
        stoi = 1
    return name, stoi

#"BothraExtendedICOHP2024"
dataset_name = "MamunHighT2019"
raw_reactions = reactions_from_dataset(dataset_name, max_count=50)
reactions = copy.deepcopy(raw_reactions)
aseify_reactions(reactions)
reactions = reactions[:10] #일단 일부만 사용

