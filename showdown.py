from flask import Flask
from flask_ask import Ask, statement, question, session
from afg import Supervisor
from random import uniform, randrange
import constants as const

app = Flask(__name__)
ask = Ask(app, '/')
sup = Supervisor('scenarios.yaml')

@ask.on_session_started
@sup.start
def new_session():
	app.logger.debug('new session started')

@sup.stop
def close_user_session():
	app.logger.debug('user session stopped')

@ask.session_ended
def session_ended():
	close_user_session()
	return '{}', 200

@ask.intent('AMAZON.HelpIntent')
def help_user():
	context_help = sup.get_help()
	return question(context_help)

@ask.launch
@sup.guide
def launched():
	return question('Welcome to Holiday Showdown. Say "start a game" to begin or "tutorial"'
					'if this is your first time')

@ask.intent('TutorialIntent')
def tutorial():
	with open('tutorial', 'r') as file:
		data = file.read().replace('\n', ' ')
	return statement(data)

@ask.intent('StartGameIntent')
@sup.guide
def start_game():
	return question('The game is starting. How many players?')

@ask.intent('DefinePlayerCountIntent', convert={'player_count': int})
@sup.guide
def define_player_count(player_count):
	if player_count < 2 or player_count > 4:
		return sup.reprompt_error('Invalid number of players. Try again.')
	session.attributes['player_count'] = player_count
	session.attributes['player_names'] = []
	return question('What is player 1\'s name')

@ask.intent('DefinePlayerNameIntent', convert={'player_name': str})
@sup.guide
def define_player_name(player_name):
	if player_name in session.attributes['player_names']:
		return sup.reprompt_error('There is already a player named ' + player_name)
	session.attributes['player_names'].append(player_name)
	if len(session.attributes['player_names']) == session.attributes['player_count']:
		return init_game()
	return sup.reprompt_error('What is player {}\'s name?'.format(
		len(session.attributes['player_names']) + 1
	))

def init_game():
	session.attributes['player_turn'] = 0
	session.attributes['cookie_count'] = []
	session.attributes['item_level'] = []
	session.attributes['store_level'] = []
	session.attributes['ad_level'] = []
	session.attributes['sabotage_level'] = []
	session.attributes['ad_mult'] = []
	session.attributes['has_done'] = []
	session.attributes['has_upgrade'] = []
	session.attributes['lose_turn'] = []
	for i in range(0, session.attributes['player_count']):
		session.attributes['cookie_count'].append(10)
		session.attributes['item_level'].append(1)
		session.attributes['store_level'].append(1)
		session.attributes['ad_level'].append(1)
		session.attributes['sabotage_level'].append(randrange(1, len(const.SABOTAGE) + 1))
		session.attributes['ad_mult'].append(0)
		session.attributes['has_done'].append(False)
		session.attributes['has_upgrade'].append(False)
		session.attributes['lose_turn'].append(False)
	return question(
		'To begin, let me set the scene. It is a cold, unforgiving winter. You have '
		'all just dropped out of college but your parents don\'t know yet, and all '
		'you can think about is holiday cookies. To make matters worse, each one of '
		'your grandma\'s got ran over by a reindeer. To pay for her medical bills, '
		'you each decide to open a holiday themed shop. You use cookies as currency '
		'and each start with 10 cookies. '
		'It is {}\'s turn '.format(session.attributes['player_names'][0])
	)

@ask.intent('UpgradeIntent', convert={'upgrade_type': str})
@sup.guide
def upgrade(upgrade_type):
	player = session.attributes['player_turn']
	cookies = session.attributes['cookie_count'][player]
	if session.attributes['has_upgrade'][player]:
		return question('You have already upgraded this turn. Try performing an action '
						'or ending your turn.')
	if upgrade_type in const.ITEM_STRINGS:
		item_level = session.attributes['item_level'][player]
		if item_level == const.ITEMS[-1][0]:
			return question('You have maxed out item upgrades. Try performing an action '
							'or ending your turn.')
		if cookies < const.ITEMS[item_level][2]:
			return question('You need ' + str(const.ITEMS[item_level][2]) + ' cookies '
							'to upgrade to ' + const.ITEMS[item_level][1] + '. Try performing '
							'an action or ending your turn.')
		session.attributes['item_level'][player] += 1
		session.attributes['cookie_count'][player] -= const.ITEMS[item_level][2]
		session.attributes['has_upgrade'][player] = True
		return question('Successfully upgraded item to ' + const.ITEMS[item_level][1] +
						'. Try performing an action or ending your turn.')
	elif upgrade_type in const.STORE_STRINGS:
		store_level = session.attributes['store_level'][player]
		if store_level == const.STORES[-1][0]:
			return question('You have maxed out store upgrades. Try performing an action '
							'or ending your turn.')
		if cookies < const.STORES[store_level][2]:
			return question('You need ' + str(const.STORES[store_level][2]) + ' cookies '
							'to upgrade to ' + const.STORES[store_level][1] + '. Try performing '
							'an action or ending your turn.')
		session.attributes['store_level'][player] += 1
		session.attributes['cookie_count'][player] -= const.STORES[store_level][2]
		session.attributes['has_upgrade'][player] = True
		return question('Successfully upgraded store to ' + const.STORES[store_level][1] +
						'. Try performing an action or ending your turn.')
	elif upgrade_type in const.AD_STRINGS:
		ad_level = session.attributes['ad_level'][player]
		if ad_level == const.ADVERTISING[-1][0]:
			return question('You have maxed out advertising upgrades. Try performing an action '
							'or ending your turn.')
		if cookies < const.ADVERTISING[ad_level][2]:
			return question('You need ' + str(const.ADVERTISING[ad_level][2]) + ' cookies '
							'to upgrade to ' + const.ADVERTISING[ad_level][1] + '. Try '
							'performing an upgrade or ending your turn.')
		session.attributes['ad_level'][player] += 1
		session.attributes['cookie_count'][player] -= const.ADVERTISING[ad_level][2]
		session.attributes['has_upgrade'][player] = True
		return question('Successfully upgraded advertising to ' +
						const.ADVERTISING[ad_level][1] + '. Try performing an action or '
						'ending your turn.')
	return question('Could not recognize upgrade option. Try again.')

@ask.intent('ActionIntent', convert={'action_type': str, 'sabotage_target': str})
@sup.guide
def action(action_type, sabotage_target):
	player = session.attributes['player_turn']
	if session.attributes['has_done'][player]:
		return question('You have already performed an action this turn. Try upgrading or '
						'ending your turn.')
	if action_type in const.AD_STRINGS:
		ad_mult = session.attributes['ad_mult']
		ad_level = session.attributes['ad_level'][player]
		advertising = const.ADVERTISING[ad_level - 1]
		mult = round(uniform(advertising[3], advertising[4]), 1)
		ad_mult[player] = round(ad_mult[player] + mult, 1)
		session.attributes['has_done'][player] = True
		return question(advertising[1] + ' added to your multiplier by ' + str(mult) +
						'. Try upgrading or ending your turn.')
	if action_type in const.SABOTAGE_STRINGS:
		if sabotage_target not in session.attributes['player_names']:
			return question('Could not recognize sabotage target. Try again.')
		target = session.attributes['player_names'].index(sabotage_target)
		if player == target:
			return question('Cannot sabotage yourself. Try again.')
		sabotage_level = session.attributes['sabotage_level'][player]
		sabotage = const.SABOTAGE[sabotage_level - 1]
		if sabotage[1] == 'spread rumors':
			session.attributes['lose_turn'][target] = True
			session.attributes['has_done'][player] = True
			return question('Rumors about ' + session.attributes['player_names'][target] +
							'\'s shop have spread. They lose their cookies this turn. '
							'Try upgrading or ending your turn.')
		elif sabotage[1] == 'anti-advertising':
			ad_mult = session.attributes['ad_mult']
			ad_mult[target] = round(ad_mult[target] - 0.5, 1)
			session.attributes['has_done'][player] = True
			return question(session.attributes['player_names'][player] + '\'s ads generated '
							'negative publicity for ' +
							session.attributes['player_names'][target] + '\'s shop. '
							'Try upgrading or ending your turn.')
		elif sabotage[1] == 'hire spy':
			if session.attributes['store_level'][target] == 1:
				return question('Cannot sabotage. Target\'s store too low. Try advertising, '
								'upgrading, or ending your turn.')
			session.attributes['store_level'][target] -= 1
			session.attributes['has_done'][player] = True
			return question(session.attributes['player_names'][player] + ' hired a spy '
							'that infiltrated ' + session.attributes['player_names'][target] +
							'\'s shop and made terrible marketing decisions. ' +
							session.attributes['player_names'][target] +
							' is forced into a store downgrade. Try upgrading or '
							'ending your turn.')
		elif sabotage[1] == 'steal items':
			if session.attributes['item_level'][target] == 1:
				return question('Cannot sabotage. Target\'s items too low. Try advertising, '
								'upgrading, or ending your turn.')
			session.attributes['item_level'][target] -= 1
			session.attributes['has_done'][player] = True
			return question(session.attributes['player_names'][player] + ', against better '
							'judgement and good business practice, breaks into ' +
							session.attributes['player_names'][target] + '\'s shop and steals '
							'everything. ' + session.attributes['player_names'][target] +
							' is forced into an item downgrade. Try upgrading or '
							'ending your turn.')
		return question('Could not recognize sabotage type. Try again.')
	return question('Could not recognize action type. Try again.')

@ask.intent('GetStatIntent', convert={'stat': str})
@sup.guide
def get_stat(stat):
	player = session.attributes['player_turn']
	if stat in const.COOKIE_STRINGS:
		cookies = session.attributes['cookie_count'][player]
		return question('You have ' + str(cookies) + ' cookies')
	elif stat in const.ITEM_STRINGS:
		item_level = session.attributes['item_level'][player]
		item = const.ITEMS[item_level - 1]
		return question('You are currently selling ' + item[1] + ' for ' +
						str(item[3]) + ' cookies per turn')
	elif stat in const.STORE_STRINGS:
		store_level = session.attributes['store_level'][player]
		store = const.STORES[store_level - 1]
		return question('You currently have a ' + store[1] + ' with a ' +
						str(store[3]) + ' multiplier')
	elif stat in const.AD_STRINGS:
		ad_level = session.attributes['ad_level'][player]
		ad = const.ADVERTISING[ad_level - 1]
		return question('Your current advertisment is ' + ad[1] + ' with a multiplier range '
						'from ' + str(ad[3]) + ' to ' + str(ad[4]))
	return question('Could not recognize what value you are asking for. Try again.')

@ask.intent('GetUpgradeCostIntent', convert={'upgrade_type': str})
@sup.guide
def get_upgrade_cost(upgrade_type):
	player = session.attributes['player_turn']
	if upgrade_type in const.ITEM_STRINGS:
		item_level = session.attributes['item_level'][player]
		item = const.ITEMS[item_level]
		return question('It costs ' + str(item[2]) + ' cookies to upgrade to ' + item[1])
	elif upgrade_type in const.STORE_STRINGS:
		store_level = session.attributes['store_level'][player]
		store = const.STORES[store_level]
		return question('It costs ' + str(store[2]) + ' cookies to upgrade to a ' + store[1])
	elif upgrade_type in const.AD_STRINGS:
		ad_level = session.attributes['ad_level'][player]
		ad = const.ADVERTISING[ad_level]
		return question('It costs ' + str(ad[2]) + ' cookies to upgrade to ' + ad[1])
	return question('Could not recognize what value you are asking for. Try again.')

@ask.intent('EndTurnIntent')
@sup.guide
def end_turn():
	player_count = session.attributes['player_count']
	player_turn = session.attributes['player_turn']
	session.attributes['player_turn'] = (player_turn + 1) % player_count
	player = session.attributes['player_turn']
	if player == 0:
		leader = end_round()
		if leader:
			return statement(leader[0] + ' is the winner with a total of ' +
							 str(leader[1]) + ' cookies')
		round_stats = ''
		for p in range(0, player_count):
			round_stats += (session.attributes['player_names'][p] + ' has ' +
						    str(session.attributes['cookie_count'][p]) + ' cookies. ')
		return question('The round is over. ' + round_stats + 'It is {}\'s turn'.format(
			session.attributes['player_names'][player]))
	return question('It is {}\'s turn'.format(session.attributes['player_names'][player]))

def end_round():
	for player in range(0, session.attributes['player_count']):
		if session.attributes['lose_turn'][player]:
			continue
		item_level = session.attributes['item_level'][player]
		store_level = session.attributes['store_level'][player]
		item_cookies = const.ITEMS[item_level - 1][3]
		ad_mult = session.attributes['ad_mult'][player]
		multiplier = 1.0 + const.STORES[store_level - 1][3] + ad_mult
		cookie_diff = int(round(item_cookies * multiplier))
		session.attributes['cookie_count'][player] += cookie_diff
	reset_round()
	cookies = session.attributes['cookie_count']
	leader = cookies.index(max(cookies))
	if cookies[leader] >= 150:
		leader_name = session.attributes['player_names'][leader]
		leader_cookies = session.attributes['cookie_count'][leader]
		return leader_name, leader_cookies
	return False

def reset_round():
	for player in range(0, session.attributes['player_count']):
		session.attributes['sabotage_level'][player] = randrange(1, len(const.SABOTAGE) + 1)
		session.attributes['ad_mult'][player] = 0.0
		session.attributes['has_upgrade'][player] = False
		session.attributes['has_done'][player] = False
		session.attributes['lose_turn'][player] = False

@ask.intent('AMAZON.CancelIntent')
def cancel():
	close_user_session()
	return statement('Cancelled')

@ask.intent('AMAZON.StopIntent')
def stop():
	close_user_session()
	return statement('Stopped')

if __name__ == '__main__':
	app.run(debug=True)
