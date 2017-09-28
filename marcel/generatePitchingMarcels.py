## Generate a full season's worth of pitching Marcel projections from past years' stats

from createTuple import createTuple ## gist: 778481
from writeMatrixCSV import writeMatrixCSV ## gist: 778484

def makePitTable(r):
    for stat in ['AB', 'H', 'D', 'T', 'HR', 'SO', 'BB', 'SF', 'HP', 'CI', 'IPouts', 'R']:
        if stat in r:   pass
        else:   r[stat] = 0
    ab = 0.9*r['IPouts'] + r['H']
    if ab == 0:
        r['AVG'] = 0
    else:
        avg = float(r['H'])/ab
        r['AVG'] = round(avg, 3)
    ip = float(r['IPouts'])/3
    era = float(r['ER']*9)/ip
    ra = float(r['R']*9)/ip
    r['ERA'] = round(era, 2)
    r['RA'] = round(ra, 2)
    r['IP'] = round(ip, 1)
    return r

def marcelPitchingSeason(yr):
    # yr = year being projected, input as int
    yr = str(yr) 
    print yr, '...'
    yr1 = str(int(yr) - 1)
    yr2 = str(int(yr) - 2)
    yr3 = str(int(yr) - 3)

    ## get list of batters; determine which pitchers are really
    ## 'pitchers' and throw out hitters with pitching lines
    projectPitchers = []
    for yr in [yr3, yr2, yr]:
        yearBatters = {}
        for p in batters:
            batID = p[0]
            if p[1] == yr:
                if p[7] == '':  continue
                else:   pass
                yearBatters[batID] = int(p[7])
            else:   pass
        for b in pitchers:
            pitID = b[0]
            if b[1] == yr:  pass
            else:   continue
            ipString = b[12]
            if ipString == '':  continue
            else:   pitIp = int(ipString)
            if pitID in yearBatters:
                if yearBatters[pitID] > pitIp: continue
                else:   pass
            else:   pass
            if pitID in projectPitchers: pass
            else:   projectPitchers.append(pitID)

    ## find league average for previous year
    yearBatters = {}
    for p in batters:
        batID = p[0]
        if p[1] == yr1:
            if p[7] == '':  continue
            else:   pass
            yearBatters[batID] = int(p[7])
        else:   pass

    leagueAverage = {}
    for b in pitchers:
        pitID = b[0]
        if b[1] == yr1:  pass
        else:   continue
        ipString = b[12]
        if ipString == '':  continue
        else:   pitIp = int(ipString)
        if pitID in yearBatters:
            if yearBatters[pitID] > pitIp: continue
            else:   pass
        else:   pass
        if pitID in projectPitchers: pass
        else:   projectPitchers.append(pitID)
        for stat in pitHeaders:
            col = pitHeaders[stat]
            try:    playerStat = int(b[col])
            except: continue
            else:   pass
            if stat in leagueAverage:
                leagueAverage[stat] += playerStat
            else:
                leagueAverage[stat] = playerStat

    for stat in pitHeaders:
        if stat in leagueAverage:   pass
        else:   leagueAverage[stat] = 0
    totalPa = leagueAverage['BFP'] ## this only works with BDB for years 1903 and later
    regression = {}
    for stat in leagueAverage:
        regression[stat] =(1200.0/totalPa)*leagueAverage[stat]

    rawProjections = {}
    ## generate projections for list of pitchers
    for b in projectPitchers:
        components = {}
        y2ip = 0
        y1ip = 0
        for stat in pitHeaders:
            components[stat] = 0
        for row in pitchers:
            if row[0] == b: pass
            else:   continue
            if row[1] == yr3:
                for stat in pitHeaders:
                    try:    playerStat = int(row[pitHeaders[stat]])
                    except: continue
                    components[stat] += playerStat
            elif row[1] == yr2:
                for stat in pitHeaders:
                    try:    playerStat = int(row[pitHeaders[stat]])
                    except: continue
                    components[stat] += 2*playerStat
                y2ip += int(row[pitHeaders['IPouts']])
            elif row[1] == yr1:
                for stat in pitHeaders:
                    try:    playerStat = int(row[pitHeaders[stat]])
                    except: continue
                    components[stat] += 3*playerStat
                y1ip += int(row[pitHeaders['IPouts']])
            else:   continue
        try:
            ggs = components['GS']/float(components['G'])
            ipReg = 75 + ggs*105
        except:
            ipReg = 120
        ## add regression component
        for stat in regression:
            components[stat] += regression[stat]
        ## get projected PA
        projIpouts = 0.5*y1ip + 0.1*y2ip + ipReg
        ## prorate into projected PA
        compIp = components['IPouts']
        prorateProj = {}
        for stat in components:
            prorateProj[stat] = (projIpouts/compIp)*components[stat]
        prorateProj['IPouts'] = projIpouts
        ## get age
        try:    age = int(yr) - int(birthYear[b])
        except: age = 29 ## in case birthyear is missing or corrupted
        ## age adjust
        if age > 29:
            ageAdj = 1/(1 + ((age - 29)*0.003))
        elif age < 29:
            ageAdj = 1 + ((29 - age)*0.006)
        else:
            ageAdj = 1
        finalProj = {}
        for stat in prorateProj:
            if stat in ['G', 'GS', 'IPouts', 'BFP']:
                finalProj[stat] = prorateProj[stat]
            elif stat in ['W', 'CG', 'SHO', 'SV', 'SO']:
                finalProj[stat] = prorateProj[stat]*ageAdj
            else:
                finalProj[stat] = prorateProj[stat]/ageAdj
        ## reliability
        reliab = 1 - (1200.0/components['BFP'])
        finalProj['rel'] = round(reliab, 2)
        finalProj['Age'] = age
        ## add to master dict
        rawProjections[b] = finalProj

    ## re-baseline
    projTotal = {}
    for pl in rawProjections:
        for stat in rawProjections[pl]:
            if stat in projTotal:
                projTotal[stat] += rawProjections[pl][stat]
            else:
                projTotal[stat] = rawProjections[pl][stat]
    projTotalPa = projTotal['BFP']
    projRatios = {}
    for stat in ['W', 'L', 'G', 'GS', 'CG', 'SHO', 'SV', 'IPouts', 'H', 'ER', 'HR', 'BB', 'SO',
                 'IBB', 'WP', 'HP', 'BK', 'R']:
        projRatios[stat] = projTotal[stat]/projTotalPa

    trueRatios = {}
    for stat in ['W', 'L', 'G', 'GS', 'CG', 'SHO', 'SV', 'IPouts', 'H', 'ER', 'HR', 'BB', 'SO',
                 'IBB', 'WP', 'HP', 'BK', 'R']:
        try:    trueRatios[stat] = leagueAverage[stat]/float(totalPa)
        except: trueRatios[stat] = 0

    marcels = {}
    for pl in rawProjections:
        marcels[pl] = {}
        for stat in rawProjections[pl]:
            if stat in ['W', 'L', 'G', 'GS', 'CG', 'SHO', 'SV', 'IPouts', 'H', 'ER', 'HR', 'BB', 'SO',
                        'IBB', 'WP', 'HP', 'BK', 'R']:
                if projRatios[stat] == 0:
                    marcels[pl][stat] = rawProjections[pl][stat]
                else:
                    marcels[pl][stat] = round((trueRatios[stat]/projRatios[stat])*rawProjections[pl][stat], 0)
            elif stat == 'BFP':
                marcels[pl][stat] = round(rawProjections[pl][stat], 0)
            else:
                marcels[pl][stat] = rawProjections[pl][stat]

##
    header = ['bdbID', 'First', 'Last', 'Year', 'age', 'rel',
              'IP', 'ERA', 'RA',  'W', 'L', 'G',
              'GS', 'CG', 'SHO', 'SV', 'H', 'ER',
              'HR', 'BB', 'SO', 'BAopp', 'IBB', 'WP', 'HP', 'BK', 'R']

    marcelSheet = [header]
    for pl in marcels:
        row = [pl]
        row += firstlast[pl]
        row.append(yr)
        marcels[pl] = makePitTable(marcels[pl])
        for stat in ['Age', 'rel',
                     'IP', 'ERA',  'RA', 'W', 'L', 'G',
                     'GS', 'CG', 'SHO', 'SV', 'H', 'ER',
                     'HR', 'BB', 'SO', 'AVG', 'IBB', 'WP', 'HP', 'BK', 'R']:
            row.append(marcels[pl][stat])
        marcelSheet.append(row)

    filename = 'marcel_pitchers_' + yr + '.csv'
    writeMatrixCSV(marcelSheet, filename)

pitHeaders = {'W': 5,
              'L': 6,
              'G': 7,
              'GS': 8,
              'CG': 9,
              'SHO': 10,
              'SV': 11,
              'IPouts': 12,
              'H': 13,
              'ER': 14,
              'HR': 15,
              'BB': 16,
              'SO': 17,
              'IBB': 20,
              'WP': 21,
              'HP': 22,
              'BK': 23,
              'BFP': 24,
              'R': 26
              }


pitchers = createTuple('bdb_pitching.csv')
## this is the pitcher seasons sheet from the lahman db.  headers:
## playerID,yearID,stint,teamID,lgID,W,L,G,GS,CG,SHO,SV,Ipouts,H,ER,HR,BB,SO,Baopp,ERA,IBB,WP,HP,BK,BFP,GF,R

batters = createTuple('bdb_batting.csv')
## this is the batting seasons sheet from the lahman db.  headers:
## playerID,yearID,stint,teamID,lgID,G,G_batting,AB,R,H,D,T,HR,RBI,SB,CS,BB,SO,IBB,HP,SH,SF,GIDP,G_old

## master db for birthYear
master = createTuple('bdb_master.csv')
## master biographical data sheet from lahman db.  headers:
## lahmanID,playerID,managerID,hofID,birthYear,birthMonth,birthDay,birthCountry,birthState,birthCity,deathYear,deathMonth,deathDay,deathCountry,deathState,deathCity,nameFirst,nameLast,nameNote,nameGiven,nameNick,weight,height,bats,throws,debut,finalGame,college,lahman40ID,lahman

birthYear = {}
for pl in master:
    birthYear[pl[1]] = pl[4]

firstlast = {}
for pl in master:
    firstlast[pl[1]] = [pl[16], pl[17]]

## sample usage 
## marcelPitchingSeason(2005)