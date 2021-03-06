# API for bloc.

# createUser()
# createMarket(marketRootId, marketBranchId, marketMin, marketMax, traderId, signingKey, verifyKey)
# createTrade(marketRootId, marketBranchId, price, quantity, traderId, signingKey, verifyKey)
# viewMarketBounds()
# viewOrderBook()


# Example POST request using Postman:

# POST /processjson HTTP/1.1
# Host: 127.0.0.1:5000
# Content-Type: application/json
# Cache-Control: no-cache
# Postman-Token: 41b1439a-0f14-4e27-aadd-8962c43aca54
#
#
# {
#     "marketRootId": 1,
#     "marketBranchId": 1,
#     "price": 0.12345,
#     "quantity": 1,
#     "traderId": 1,
#     "signingKey": "2e22f9ce7c984a93a27f126a23d62fbc50a2cb5b28ea578c8a0f4e8fba8de2e9",
#     "traderId": 4,
#     "verifyKey": "d9caa2ad98e883c283e589401c67d6c091e8970f84b18fa72c82d4b4d5d6e330"
#
# }

# Example POST request from python using requests

# content = {"signingKey": "42b45efe8e50d5161ad1cfaba2e3de37387109f0f6b4451b1c94a7a4f7ae5ec8",
#  "traderId": 4, "verifyKey": "05e0ed41fdda6f705a1926a2803ac77189400f987feb5e7bb33cca38ae8be2da",
#  "marketRootId": 5, "marketBranchId": 1, "marketMin": 1, "marketMax":1.444}
# url = 'http://127.0.0.1:5000/createMarket'
# headers = {'content-type': 'application/json'}
# response = requests.post(url, data=json.dumps(content), headers=headers)
# pd.DataFrame(response.json(), index=[0])

from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import validators, StringField, PasswordField
from wtforms.fields.html5 import EmailField
import requests

from bloc.BlocServer import BlocServer
from bloc.BlocClient import BlocClient
from bloc.BlocTime import BlocTime
import json
import numpy as np
import pandas as pd
import traceback
from datetime import datetime

app = Flask(__name__)

# set later as Herokou env variable
app.config['SECRET_KEY'] = "ASNDFC283RYCOIWSJFCASR73CRASFCW3HRCNIWHRCIASHC73HRC";

# Running this in the end to avoid issues
def runapp():
    if __name__ == "__main__":
        app.jinja_env.auto_reload = True
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        app.run(debug=True)


class SignupForm(FlaskForm):
    first_name = StringField('First Name', [validators.DataRequired()])
    last_name = StringField('Last Name', [validators.DataRequired()])
    email = EmailField('Email', [validators.DataRequired(), validators.Email()])
    password = PasswordField('Password', [validators.DataRequired()])
    confirm_password = PasswordField('Confirm Password', [validators.DataRequired(),validators.EqualTo('password', message='Passwords must match')])

class LoginForm(FlaskForm):
    email = EmailField('Email', [validators.DataRequired()])
    password = PasswordField('Password', [validators.DataRequired()])


"""
/////////////////////////////
//  Template ROUTES
/////////////////////////////
"""

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/markets')
def markets():
    url = 'https://blocmarket.herokuapp.com/viewMarketBounds'
    response = requests.post(url, data=json.dumps({}), headers={'content-type': 'application/json'})
    jsonData = json.loads(response.json())
    return render_template('markets.html', markets=jsonData)

@app.route('/markets/<num>')
def market(num):
    # url = 'https://blocmarket.herokuapp.com/viewMarketBounds'
    # response = requests.post(url, data=json.dumps({}), headers={'content-type': 'application/json'})
    # jsonData = json.loads(response.json())
    url = 'https://blocmarket.herokuapp.com/viewOrderBook'
    content = {'marketId': int(num)}
    response = requests.post(url, data=json.dumps(content), headers={'content-type': 'application/json'})
    orderbookData = json.loads(response.json())
    url2 = 'https://blocmarket.herokuapp.com/viewOpenTrades'
    response2 = requests.post(url, data=json.dumps(content), headers={'content-type': 'application/json'})
    openTradesData = json.loads(response.json())
    # print(orderbookData)

    return render_template('market.html', num=num, orderbookData=orderbookData, openTradesData=openTradesData)

@app.route('/signup', methods = ['POST','GET'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        print('is successful')
        first_name = form.first_name.data
        last_name = form.last_name.data
        email = form.email.data
        password = form.password.data
        confirm_password = form.confirm_password.data

        # return redirect(url_for('index'))

    # if request.method == 'POST':
    #     print(request.form.get('first_name'))
    return render_template('/accounts/signup.html', form=form)

@app.route('/login', methods = ['POST'])
def login():
    form = SignupForm()
    if form.validate_on_submit():
        print('is successful')

    return render_template('/accounts/login.html', form=form)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


"""
/////////////////////////////
//  API ROUTES
/////////////////////////////
"""

@app.route('/createUser', methods=['POST', 'GET'])
def createUser():
    bs = BlocServer()
    bc = BlocClient()
    bc.generateSignatureKeys()
    newUsr = bc.createUser_client(blocServer=bs)
    bs.conn.close()

    return jsonify({'traderId': str(newUsr['traderId']),
                    'verifyKey': newUsr['verifyKey'],
                    'signingKey': bc.signingKey})



@app.route('/createMarket', methods=['POST'])
def createMarket():
    #  Get request data
    data = request.get_json()
    # Instantiate market objects
    bs = BlocServer()
    bc = BlocClient()
    # Retrieve keys from session and assign in client
    bc.signingKey = data['signingKey']
    bc.verifyKey = data['verifyKey']

    if 'marketDesc' in data:
        marketRow = pd.DataFrame(data, index=[0])[['marketRootId', 'marketBranchId','marketMin', 'marketMax','traderId', 'marketDesc']]
    else:
        marketRow = pd.DataFrame(data, index=[0])[['marketRootId', 'marketBranchId','marketMin', 'marketMax','traderId']]

    # Call createMarket_client
    try:
        checks, allChecks = bc.createMarket_client(marketRow=marketRow, blocServer=bs)
    except:
        checks = traceback.format_exc()
        allChecks = {'Boned':True, 'marketId':0}

    bs.conn.close()

    return jsonify({'checks': str(checks),
                    'marketId': int(allChecks['marketId']),
                    'marketRootId': data['marketRootId'],
                    'marketBranchId': data['marketBranchId'],
                    'marketMin': data['marketMin'],
                    'marketMax': data['marketMax'],
                    'traderId': data['traderId'],
                    'allChecks': str(allChecks)})


@app.route('/createTrade', methods=['POST'])
def createTrade():
    #  Get request data
    data = request.get_json()
    # Instantiate market objects
    bs = BlocServer()
    bc = BlocClient()
    # Retrieve keys from session and assign in client
    bc.signingKey = data['signingKey']
    bc.verifyKey = data['verifyKey']
    tradeRow = pd.DataFrame(data, index=[0])[['marketId', 'price', 'quantity', 'traderId']]
    # Call createMarket_client
    try:
        checks, allChecks = bc.createTrade_client(tradeRow=tradeRow, blocServer=bs)
    except Exception as err:
        checks = traceback.format_exc()
        allChecks = {'Boned':True}



    bs.conn.close()
    if np.isnan(allChecks['tradeId']):
        allChecks['tradeId'] = 0

    return jsonify({'checks': str(checks),
                    'tradeId': int(allChecks['tradeId']),
                    'marketId': data['marketId'],
                    'price': data['price'],
                    'quantity': data['quantity'],
                    'traderId': data['traderId'],
                    'allChecks': str(allChecks)})

# View market bounds
@app.route('/viewMarketBounds', methods=['POST'])
def viewMarkets():
    # Return market bounds
    bs = BlocServer()
    mB = pd.read_sql_table('marketBounds', bs.conn)
    mT = pd.read_sql_table('marketTable', bs.conn)

    # Add original market descriptions
    minTimeInd  = mT.groupby('marketId').agg({'timeStampUTC': 'idxmin'})['timeStampUTC']
    originalMarketDescriptions = mT.loc[minTimeInd, ['marketId', 'marketDesc']]
    mB = mB.merge(originalMarketDescriptions, on='marketId',how='left')

    bs.conn.close()

    return jsonify(mB.loc[:,['marketId', 'marketRootId', 'marketBranchId', 'marketMin', 'marketMax', 'marketDesc']].to_json())

# View order book
@app.route('/viewOrderBook', methods=['POST'])
def viewOrderBook():
    #  Get request data
    data = request.get_json()
    marketId = data['marketId']
    # Return order book
    bs = BlocServer()
    oB = pd.read_sql_table('orderBook', bs.conn)
    oB = oB[np.logical_not( oB['iRemoved']) & (oB['marketId']==marketId)]
    bs.conn.close()

    return jsonify(oB.loc[:,['tradeId','marketId', 'price', 'quantity', 'traderId', 'iMatched', 'timeStampUTC']].to_json())


# View order book
@app.route('/viewOpenTrades', methods=['POST'])
def viewOpenTrades():
    #  Get request data
    data = request.get_json()
    marketId = data['marketId']
    # Return order book
    bs = BlocServer()
    oB = pd.read_sql_table('orderBook', bs.conn)

    # Open trades
    openTrades = oB[np.logical_not(oB['iMatched']) & np.logical_not(oB['iRemoved']) & (oB['marketId']==marketId)]

    bs.conn.close()

    return jsonify(openTrades.loc[:,['tradeId','marketId', 'price', 'quantity', 'traderId', 'timeStampUTC']].to_json())

# View order book
@app.route('/viewMatchedTrades', methods=['POST'])
def viewMatchedTrades():
    #  Get request data
    data = request.get_json()
    marketId = data['marketId']
    # Return order book
    bs = BlocServer()
    oB = pd.read_sql_table('orderBook', bs.conn)

    # Open trades
    matchedTrades = oB[oB['iMatched'] & oB['marketId']==marketId]
    # Sum orders with same price by quantity
    matchedTrades_sum = matchedTrades.groupby(['marketId', 'price', 'traderId'], as_index=False).agg({"quantity": "sum"})
    bs.conn.close()

    return jsonify(matchedTrades_sum.loc[:, ['marketId', 'price', 'quantity', 'traderId']].to_json())


# Trade summary
@app.route('/viewTradeSummary', methods=['POST'])
def viewTradeSummary():

    data = request.get_json()
    traderId = data['traderId']
    bs = BlocServer()
    #ps = pd.read_sql_query('SELECT "price", "quantity", "traderId", "isMatched", "timeStampUTC", "marketId", "marketRootId", "marketBranchId", "marketMin", "marketMax" FROM "orderBook" INNER JOIN "marketTable" ON "orderBook.marketId" WHERE "traderId" = %s' % (str(traderId)), bs.conn)
    oB = pd.read_sql_table('orderBook', bs.conn)
    mT = pd.read_sql_table('marketBounds', bs.conn)

    tradeSummary = oB[np.logical_and(np.logical_not(oB['iRemoved']),oB['traderId'] == traderId)]

    posSummary = pd.merge(tradeSummary.loc[:,['tradeId','marketId', 'price', 'quantity', 'traderId', 'iMatched', 'timeStampUTC']], mT.loc[:, ['marketId', 'marketRootId', 'marketBranchId', 'marketMin', 'marketMax']], on='marketId', how='left')

    posSummary['marketMinOutcome'] = (posSummary['marketMin'] - posSummary['price'])*posSummary['quantity']
    posSummary['marketMaxOutcome'] = (posSummary['marketMax'] - posSummary['price'])*posSummary['quantity']

    return jsonify(posSummary.to_json())

@app.route('/viewTickHistory', methods=['POST'])
def viewTickHistory():
    #  Processed tick data with self
    data = request.get_json()
    marketId = data['marketId']
    # Start and end time expected as unix timestamps in UTC
    startTime = data['startTime']
    endTime = data['endTime']
    # Convert dates to datetime (Use UTC stamp * 1000 format so it's consistent with what comes back from datetimes)
    startTime = datetime.fromtimestamp(startTime/1000)
    endTime = datetime.fromtimestamp(endTime/1000)
    # Return order book
    bs = BlocServer()
    oB = pd.read_sql_table('orderBook', bs.conn)
    oB = oB.loc[(oB['marketId']==marketId) & (oB['timeStampUTC'] > startTime) & (oB['timeStampUTC']< endTime)]
    # Sort by timeStampId
    oB = oB.sort_values(by=['timeStampUTC'], ascending=True)
    # numpy this or it's super slow
    p = oB['price'].values
    q = oB['quantity'].values
    tradeId = oB['tradeId'].values
    traderId = oB['traderId'].values
    iMatched = oB['iMatched'].values
    ts = oB['timeStampUTC'].values
    xTradeId = tradeId*np.nan
    ownCross = tradeId*False
    ownTrade = tradeId*False

    for iRow in range(len(p)):
        if iMatched[iRow]:
            # Find matching trade
            mask = (p == p[iRow]) & (q == -1*q[iRow]) & (ts > ts[iRow])
            if mask.any():
                # Get first crossing trade and check if own trade
                xTdId = tradeId[mask][0]
                iOwnTrade = traderId[iRow] == traderId[mask][0]
                # Record info
                xTradeId[iRow] = xTdId
                xTradeId[mask] = tradeId[iRow]
                ownCross[mask] = iOwnTrade
                ownTrade[mask] = iOwnTrade
                ownTrade[iRow] = iOwnTrade

    oB['xTradeId'] = xTradeId
    oB['ownCross'] = ownCross
    oB['ownTrade'] = ownTrade

    # History of bids and asks excluding own crosses
    bids = oB.loc[~oB['ownCross'] & (oB['quantity'] > 0), :].sort_values(by='price', ascending=False)
    asks = oB.loc[~oB['ownCross'] & (oB['quantity'] < 0), :].sort_values(by='price', ascending=False)
    trades = oB.loc[~oB['ownTrade'] & oB['iMatched'], :].sort_values(by='price', ascending=False)

    bids['tickType'] = 'BID'
    asks['tickType'] = 'ASK'
    trades['tickType'] = 'TRADE'

    tickHistory = pd.concat([bids, asks, trades]).sort_values(by='timeStampUTC')
    tickHistory.reset_index(inplace=True)

    bs.conn.close()

    return jsonify(tickHistory[['tickType','tradeId', 'xTradeId' ,'marketId', 'price', 'quantity', 'traderId', 'iMatched', 'timeStampUTC']].to_json())

@app.route('/checkCollateral', methods=['POST'])
def checkCollateral():
    # Will work with or without price/quantity/market
    data = request.get_json()

    if 'price' in data:
        price = data['price']
        quantity = data['quantity']
        marketId = data['marketId']
        traderId = data['traderId']
    elif 'traderId' in data:
        price = []
        quantity = []
        marketId = []
        traderId = data['traderId']
    else:
        return jsonify({'colChk': 'No input'})


    bs = BlocServer()
    bs.updateOutcomeCombinations()
    colChk, collateralDetails = bs.checkCollateral(p_=price, q_=quantity, mInd_=marketId, tInd_= traderId )
    worstCollateral = np.min(collateralDetails['worstCollateral'])

    return jsonify({'colChk': str(colChk),
                    'traderId': traderId,
                    'price': price,
                    'quantity': quantity,
                    'marketId': marketId,
                    'outcomes': str(collateralDetails['outcomes']),
                    'worstCollateral': worstCollateral})

# Local time server
@app.route('/getSignedUTCTimestamp')
def getSignedUTCTimestamp():
    # Get a signed timestamp
    bt = BlocTime()
    signedUTCNow = bt.signedUTCNow()

    tsOutput = {'timeStampUTC': str(signedUTCNow['timeStampUTC']),
                             'timeStampUTCSignature': str(signedUTCNow['timeStampUTCSignature']),
                             'verifyKey': signedUTCNow['verifyKey']}
    return json.dumps(tsOutput)

# SP functions

@app.route('/createSPEvent', methods=['POST', 'GET'])
def createSPEvent():
    # Get event data and append to database
    data = request.get_json()
    bs = BlocServer()
    newEvent = pd.DataFrame({'sport': [data['sport']],
                                  'competition': [data['competition']],
                                  'event': [data['event']],
                                  'starttimestamputc': [data['starttimestamputc']]})
    newEvent.to_sql(name='spevent', con=bs.conn, if_exists='append', index=False)

    eventid = pd.read_sql_query('select max("eventid") from "spevent"', bs.conn)['max'][0]


    return jsonify({'eventid': str(eventid)})


'''
@app.route('/createSPOutcome', methods=['POST', 'GET'])
def createSPOutcome():
    # Get event data and append to database
    data = request.get_json()
    bs = BlocServer()
    #TODO: this query doesn't work. Check on JSON updates
    bs.conn.execute(
        'update "spevent" set "outcome" = \' %s \' where "eventid" = %s' % (data['outcome'], data['eventid']))

    #queryout = pd.read_sql_query('update "spevent" set "outcome" = json_build_object("0",10,"1",15) where "eventid"=%s' % (data['eventid']), bs.conn)
    return jsonify({'updated': True})
'''

@app.route('/createSPMarket', methods=['POST', 'GET'])
def createSPMarket():
    # Get market data and append to database
    data = request.get_json()
    bs = BlocServer()
    newMarket = pd.DataFrame({'eventid': [data['eventid']],
                            'markettype': [data['markettype']],
                            'runners': [data['runners']],
                            'marketparameters': [data['marketparameters']],
                            'notes': [data['notes']]})
    newMarket.to_sql(name='spmarket', con=bs.conn, if_exists='append', index=False)
    marketid = pd.read_sql_query('select max("marketid") from "spmarket"', bs.conn)['max'][0]
    return jsonify({'marketid': str(marketid)})

@app.route('/createSPRecord', methods=['POST', 'GET'])
def createSPRecord():
    # Get record data and append to database
    data = request.get_json()
    bs = BlocServer()
    newRecord = pd.DataFrame({'source': [data['source']],
                            'marketid': [data['marketid']],
                            'runnerid': [data['runnerid']],
                            'timestamputc': [data['timestamputc']],
                            'handicap': [data['handicap']],
                            'odds': [data['odds']],
                            'stake': [data['stake']],
                            'islay': [data['islay']],
                            'isplaced': [data['isplaced']],
                            'notes': [data['notes']]})
    newRecord.to_sql(name='sprecord', con=bs.conn, if_exists='append', index=False)
    recordid = pd.read_sql_query('select max("recordid") from "sprecord"', bs.conn)['max'][0]
    return jsonify({'recordid': str(recordid)})


@app.route('/createSPScore', methods=['POST', 'GET'])
def createSPScore():
    # Get record data and append to database
    data = request.get_json()
    bs = BlocServer()
    newScore = pd.DataFrame({'eventid': [data['eventid']],
                            'runnerid': [data['runnerid']],
                            'timestamputc': [data['timestamputc']],
                            'measure': [data['measure']],
                            'value': [data['value']],
                            'isfinal': [data['isfinal']]})
    newScore.to_sql(name='spscore', con=bs.conn, if_exists='append', index=False)
    scoreid = pd.read_sql_query('select max("scoreid") from "spscore"', bs.conn)['max'][0]
    return jsonify({'scoreid': str(scoreid)})

# Views
# Trade summary
@app.route('/viewSPEvents', methods=['POST', 'GET'])
def viewSPEvents():

    data = request.get_json()
    bs = BlocServer()
    spevents = pd.read_sql_table('spevent', bs.conn)
    return jsonify(spevents.to_json())

@app.route('/viewSPMarkets', methods=['POST', 'GET'])
def viewSPMarkets():

    data = request.get_json()
    bs = BlocServer()
    spmarkets = pd.read_sql_table('spmarket', bs.conn)
    return jsonify(spmarkets.to_json())

@app.route('/viewSPRecords', methods=['POST', 'GET'])
def viewSPRecords():

    data = request.get_json()
    bs = BlocServer()
    sprecords = pd.read_sql_table('sprecord', bs.conn)
    return jsonify(sprecords.to_json())

@app.route('/viewSPScores', methods=['POST', 'GET'])
def viewSPScores():

    data = request.get_json()
    bs = BlocServer()
    spscores = pd.read_sql_table('spscore', bs.conn)
    return jsonify(spscores.to_json())



runapp()
