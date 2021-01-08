#!/usr/local/bin/python3
from html.parser import HTMLParser
from collections import OrderedDict
import requests, json, itertools, random, csv, os

SEARCH = False
MAX_SEARCH_PAGES = 20

GET_DECKS = False

IGNORED_DECK_IDS = [
  '',
]
EXPORT_DECKS = False

UPDATE_COLLECTION = False

FIND_COMBINATIONS = True
SHUFFLE_DECKS = True    # Should only be set to False if known

CORP = True
MAX_DECKS_PER_CORP = 6
NUM_CORP_ITERATIONS = 10
CORP_INCLUDED = {
  'haas-bioroid' : True,
  'jinteki' : True,
  'nbn' : True,
  'weyland-consortium' : True,
}

RUNNER = True
MAX_DECKS_PER_RUNNER = 6
NUM_RUNNER_ITERATIONS = 20
RUNNER_INCLUDED = {
  'anarch' : True,
  'criminal' : True,
  'shaper' : True,
  'apex' : False,
  'adam' : False,
  'sunny-lebeau' : False,
}

# pack_code: (netrunnerdb_search_string_id, qty)
packs = {
  'core'  : ('1', 2),   # core set
  'wla'   : ('2', 1),   # what lies ahead
  'ta'    : ('3', 1),   # trace amount
  'ce'    : ('4', 0),   # cyber exodus
  'asis'  : ('5', 1),   # a study in static
  'hs'    : ('6', 0),   # humanity's shadow
  'fp'    : ('7', 0),   # future proof
  'cac'   : ('8', 1),   # creation and control
  'om'    : ('9', 0),   # opening moves
  'st'    : ('10', 0),  # second thoughts
  'mt'    : ('11', 0),  # mala tempora
  'tc'    : ('12', 0),  # true colors
  'dt'    : ('18', 1),  # double time
  'fal'   : ('19', 1),  # fear and loathing
  'draft' : ('20', 0),  # draft
  'hap'   : ('21', 1),  # honor and profit
  'up'    : ('22', 0),  # upstalk
  'tsb'   : ('23', 1),  # the spaces between
  'fc'    : ('24', 0),  # first contact
  'uao'   : ('25', 0),  # up and over
  'atr'   : ('26', 0),  # all that remains
  'ts'    : ('27', 0),  # the source
  'oac'   : ('28', 1),  # order and chaos
  'val'   : ('29', 1),  # the valley
  'bb'    : ('30', 1),  # breaker bay
  'cc'    : ('31', 0),  # chrome city
  'uw'    : ('32', 1),  # the underway
  'oh'    : ('33', 0),  # old hollywood
  'uot'   : ('34', 0),  # the universe of tomorrow
  'dad'   : ('35', 1),  # data and destiny
  'kg'    : ('36', 0),  # kala ghoda
  'bf'    : ('37', 1),  # business first
  'dag'   : ('38', 0),  # democracy and dogma
  'si'    : ('39', 0),  # salsette island
  'tlm'   : ('40', 0),  # the liberated mind
  'ftm'   : ('41', 0),  # fear the masses
  '23s'   : ('42', 1),  # 23 seconds
  'em'    : ('43', 1),  # blood money
  'es'    : ('44', 1),  # escalation
  'in'    : ('45', 1),  # intervention
  'ml'    : ('46', 0),  # martial law
  'qu'    : ('47', 0),  # quorum
  'dc'    : ('48', 0),  # daedalus complex
  'so'    : ('49', 0),  # station one
  'eas'   : ('50', 1),  # earth's scion
  'td'    : ('51', 1),  # terminal directive
  'baw'   : ('52', 1),  # blood and water
  'fm'    : ('53', 0),  # free mars
  'cd'    : ('54', 1),  # crimson dust
  'core2' : ('55', 1),  # revised core set
  'ss'    : ('56', 0),  # sovereign sight
  'dtwn'  : ('57', 1),  # down the white nile
  'cotc'  : ('58', 1),  # council of the crest
  'tdatd' : ('59', 1),  # the devil and the dragon
  'win'   : ('60', 0),  # whispers in nalubaale
  'ka'    : ('61', 1)   # kampala ascendant
  'rar'   : ('62', 1),  # reign and reverie
  'mo'    : ('63', 0),  # magnum opus
  'napd'  : ('64', 0),  # NAPD multiplayer
  'sc19'  : ('65', 0),  # system core 19
  'df'    : ('67', 0),  # downfall
  'ur'    : ('68', 0),  # uprising
  'urbp'  : ('69', 0),  # uprising booster pack
  'mor'   : ('80', 0),  # magnum opus reprint
}

extra_cards = {
  '06095' : 1,
}

# other purchases made - not included in search parameters
# 2015 world championships HB engineering the future
# 2015 world championships valencia (anarch)


class MyDeckParser(HTMLParser):

  decks = set()

  def handle_starttag(self, tag, attrs):
    if tag == 'a':
      for attr in attrs:
        if attr[0] == 'href' and attr[1].startswith('/en/decklist/'):
          self.decks.add(attr[1].split('/')[3])

def write_cards(card_filename, headers = None):
  print('Downloading Cards...')
  cards = OrderedDict()
  url = 'https://netrunnerdb.com/api/2.0/public/cards'
  r = requests.get(url, headers=headers)

  all_cards = r.json()['data']
  for card in all_cards:
    cards[card['code']] = card
    if 'image_url' not in cards[card['code']]:
      cards[card['code']]['image_url'] = 'https://netrunnerdb.com/card_image/'+card['code']+'.png'
    cards[card['code']]['maps_to'] = set()

  # Need to perform check of card names to map core to revised core
  for card_counter in cards:
    for comparison_card in cards:
      if cards[card_counter]['title'] == cards[comparison_card]['title'] and card_counter != comparison_card:
        cards[card_counter]['maps_to'].add(comparison_card)
        cards[comparison_card]['maps_to'].add(card_counter)

  for card in all_cards:
    cards[card['code']]['maps_to'] = list(cards[card['code']]['maps_to'])

  # Write to file
  with open(card_filename, 'w') as f:
    f.write(json.dumps(cards, indent=2))

  return card_filename

def search_results(payloads, headers = None, max_pages = 40):
  print('Searching NetRunnerDB...')
  parser = MyDeckParser()
  try:
    payload_counter = 0
    for payload in payloads:
      payload_counter += 1
      for page in range(1,max_pages+1):
        print('processing payload',payload_counter,'page',page)
        url = 'https://netrunnerdb.com/en/decklists/find'
        if page != 1:
          url += '/' + str(page)

        r = requests.get(url, headers=headers, params=payload)
        parser.feed(r.text)

    return parser.decks

  except Exception as e:
      print(e.code)
      print(e.read())

def write_id_file(parser_result,filename):
  print('Writing Deck IDs to File...')
  with open(filename,'w') as f:
    for deck_id in parser_result:
      f.write(deck_id+"\n")
  return filename

def write_decks(id_filename, deck_filename, headers = None):
  print('Downloading Decks...')
  decks = OrderedDict()
  with open(id_filename) as f:
    for id in f:
      id = id.strip()
      print('Processing',id)

      # Use NetrunnerDB API
      url = 'https://netrunnerdb.com/api/2.0/public/decklist/'+id
      r = requests.get(url, headers=headers)

      decks[id] = r.json()['data'][0]

    # Write to file
    with open(deck_filename, 'w') as f:
      f.write(json.dumps(decks, indent=2))

  return deck_filename

def identify_deck_factions(deck_filename, cards_filename):
  print('Identifying Deck Factions...')
  with open(deck_filename) as f:
    decks = json.load(f)
  with open(cards_filename) as f:
    cards = json.load(f)
  for deck in decks:
    decks[deck]['side_code'] = ''
    decks[deck]['faction_code'] = ''
    deck_cards = decks[deck]['cards']
    for card in deck_cards:
      deck_card = cards[card]
      if deck_card['type_code'] == 'identity':
        decks[deck]['side_code'] = deck_card['side_code']
        decks[deck]['faction_code'] = deck_card['faction_code']

  with open(deck_filename, 'w') as f:
    f.write(json.dumps(decks, indent=2))

  return deck_filename

def construct_collection(cards_filename, collection_filename, packs, extra_cards):
  print('Constructing Collection...')
  collection = OrderedDict()
  with open(cards_filename) as f:
    cards = json.load(f)
    for card in cards:
      pack_code = cards[card]['pack_code']
      collection_ids = cards[card]['maps_to']
      if pack_code in packs or card in extra_cards:
        if len(cards[card]['maps_to']) > 0:
          collection_ids.append(cards[card]['code'])
          collection_ids = tuple(sorted(collection_ids))
        else:
          collection_ids = (cards[card]['code'],)
        if pack_code in packs:
          collection[collection_ids] = collection.get(collection_ids, 0) + (cards[card]['quantity'] * packs[pack_code][1])
        else:
          collection[collection_ids] = collection.get(collection_ids, 0) + extra_cards[card]

  collection2 = OrderedDict()
  for key in collection:
    collection2[key[0]] = collection[key]

  # Write to file
  with open(collection_filename, 'w') as f:
    f.write(json.dumps(collection2, indent=2))

  return collection_filename

def select_decks(decks, included, ignored, max, shuffle = True):
  selected = []
  deck_ids = list(decks)
  if shuffle:
    random.shuffle(deck_ids)
  for faction in included:
    if included[faction]:
      selected.append([d for d in deck_ids if (included[faction] and decks[d]['faction_code'] == faction)][:max])
  return selected

def find_combinations(side, iteration, cards, collection, decks):
  print('Determining valid combinations for', side, 'iteration', iteration)
  valid = {
    'valid': {},
    'invalid': {}
  }
  for combo in itertools.product(*decks):
    combo_result = check_combination(cards, combo, collection)
    if len(combo_result) == 0:
      valid['valid'][','.join(combo)] = combo_result
    else:
      valid['invalid'][','.join(combo)] = combo_result

  return valid

def check_combination(cards, deck_combination, collection):
  all_cards = {}
  missing_cards = {}
  for deck in deck_combination:
    for card in decks[deck]['cards']:
      quantity = decks[deck]['cards'][card]

      # Check for alternate card codes
      card_ids = cards[card]['maps_to']
      if len(card_ids) > 0:
        card_ids.append(cards[card]['code'])
        card_ids = tuple(sorted(card_ids))
      else:
        card_ids = (cards[card]['code'],)
      card_code = card_ids[0]
      all_cards[card_code] = all_cards.get(card_code,0) + quantity
  for card in all_cards:
    if card not in collection:
      missing_qty = all_cards[card]
    else:
      missing_qty = all_cards[card] - collection[card]
    if missing_qty > 0:
      missing_cards[card] = missing_qty
  return missing_cards

if SEARCH:

  headers = {
    'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1.2 Safari/605.1.15',
    'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
  }

  # Search data
  payloads = [
    {
      'faction' : '',
      'sort' : 'popularity',
      'rotation_id' : '',
      'author' : '',
      'title' : '',
      'is_legal' : '',
      'mwl_code' : '',
      'packs[]' : [packs[p][0] for p in packs],
    }
  ]

# old payload for big boxes only
#    {
#      'faction' : '',
#      'sort' : 'popularity',
#      'rotation_id' : '',
#      'author' : 'filk',
#      'title' : '',
#      'is_legal' : '',
#      'mwl_code' : '',
#      'packs[]' : ['1', '8', '21', '28', '35', '51, '55', '62'],
#    }

  # Grab all card info json
  cards_file = write_cards('cards.json', headers)

  # Perform search on NetrunnerDB
  results = search_results(payloads, headers, MAX_SEARCH_PAGES)

  # Store deck ids in a file (so we don't need to request every time)
  id_file = write_id_file(results,'deck_ids.txt')

if GET_DECKS:
  # Generate deck json from IDs
  decks_file = write_decks(id_file,'decks.json', headers)

  # Identify deck factions
  decks_file = identify_deck_factions('decks.json','cards.json')

if EXPORT_DECKS:
  decks_file = 'decks.json'
  with open(decks_file) as f:
    decks = json.load(f)
  with open('all_deck_info.csv', 'w') as f:
    writer = csv.DictWriter(f, fieldnames=decks[[d for d in decks][0]].keys())
    for deck in decks:
      writer.writerow(decks[deck])

if UPDATE_COLLECTION:
  # Construct collection (available cards)
  collection_file = construct_collection('cards.json', 'collection.json', packs, extra_cards)

if FIND_COMBINATIONS:

  collection_file = 'collection.json'
  cards_file = 'cards.json'
  decks_file = 'decks.json'
  valid_corp_file = 'valid_corp_combinations.json'
  valid_runner_file = 'valid_runner_combinations.json'

  # reload collection
  with open(collection_file) as f:
    collection = json.load(f)

  # reload cards
  with open(cards_file) as f:
    cards = json.load(f)

  # reload decks
  with open(decks_file) as f:
    decks = json.load(f)

  if CORP:

    valid_corp_combos = {}
    invalid_corp_combos = {}

    for i in range(NUM_CORP_ITERATIONS):

      iteration_file = valid_corp_file.split('.')[0]+str(i)+'.txt'

      while True:
        corp_decks = select_decks(decks, CORP_INCLUDED, IGNORED_DECK_IDS, MAX_DECKS_PER_CORP, SHUFFLE_DECKS)
        deck_analysis = find_combinations('corp', i, cards, collection, corp_decks)

        for v in deck_analysis['invalid']:
          invalid_corp_combos[v] = deck_analysis['invalid'][v]
        for v in deck_analysis['valid']:
          valid_corp_combos[v] = deck_analysis['valid'][v]
        # Break the loop if we have a valid combination, otherwise try again
        if len(deck_analysis['valid']) > 0:
          break

    valid_corp_combos2 = OrderedDict()
    for key in sorted(valid_corp_combos):
      valid_corp_combos2[key] = valid_corp_combos[key]

    invalid_corp_combos2 = OrderedDict()
    for key in sorted(invalid_corp_combos):
      invalid_corp_combos2[key] = invalid_corp_combos[key]

    with open('valid_corp_combinations.txt', 'w') as f:
      findings = {
        'valid' : valid_corp_combos2,
        'invalid' : invalid_corp_combos2,
      }
      f.write(json.dumps(findings, indent=2))

  if RUNNER:

    valid_runner_combos = {}
    invalid_runner_combos = {}

    for i in range(NUM_RUNNER_ITERATIONS):

      iteration_file = valid_runner_file.split('.')[0]+str(i)+'.txt'

      while True:
        runner_decks = select_decks(decks, RUNNER_INCLUDED, IGNORED_DECK_IDS, MAX_DECKS_PER_RUNNER, SHUFFLE_DECKS)
        deck_analysis = find_combinations('runner', i, cards, collection, runner_decks)

        for v in deck_analysis['invalid']:
          invalid_runner_combos[v] = deck_analysis['invalid'][v]
        for v in deck_analysis['valid']:
          valid_runner_combos[v] = deck_analysis['valid'][v]
        # Break the loop if we have a valid combination, otherwise try again
        if len(deck_analysis['valid']) > 0:
          break

    valid_runner_combos2 = OrderedDict()
    for key in sorted(valid_runner_combos):
      valid_runner_combos2[key] = valid_runner_combos[key]

    invalid_runner_combos2 = OrderedDict()
    for key in sorted(invalid_runner_combos):
      invalid_runner_combos2[key] = invalid_runner_combos[key]

    with open('valid_runner_combinations.txt', 'w') as f:
      findings = {
        'valid' : valid_runner_combos2,
        'invalid' : invalid_runner_combos2,
      }
      f.write(json.dumps(findings, indent=2))
