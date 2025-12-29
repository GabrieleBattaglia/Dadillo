# Data concepimento venerdì 8 febbraio 2019.
# Ringraziamenti:
# queste persone mi hanno gentilmente aiutato durante lo sviluppo di questo software.
# Bersan Vrioni, Marco De Paoli, Emanuela Pontiroli, ChatGPT e Gemini.
# Dadillo, a DiceWorld Tournament Manager, by Gabriele Battaglia, ChatGPT e Gemini.
import itertools, time, sys, json, functools
from GBUtils import dgt, key
TEMPO=time.time()
VERSIONE="1.0.4, di dicembre 2025."
FIELDS=['Nome','Punti','Vittorie','Pareggi','Sconfitte']
# Funzione per convertire le chiavi numeriche di un dizionario (che in json vengono caricate come stringhe)
def conv_key_int(d): 
	return {int(k):v for k,v in d.items()}
def Coppie(g,pi,k,n=""):
	'''riceve giocatori, lista partite incomplete e la chiave per il dizionario delle pi
	aggiunge abbinamenti (solo quelli che includono il nuovo giocatore se n è non vuota)'''
	for j in itertools.permutations(g.keys(),2):
		if n!="":
			if n in j:
				pi[k]=j
				k+=1
		else:
			pi[k]=j
			k+=1
	return pi
def Agggioc(g,pi,k):
	'''aggiunge un giocatore e aggiorna le partite incomplete'''
	print("Yeahh, nuova carne fresca per il tuo seguito, o mio incommensurabile monte di magnificenza. Bene bene!")
	while True:
		nome=dgt("Qual è il nome del nuovo adepte? ",kind="s",smin=1,smax=16)
		nome=nome.title()[:16]
		if nome in g:
			print(f"Mi scudiscio per la vergogna, mio onorato ma {nome} l'abbiamo già convertito al nostro volere. Dimmene un altro.")
		else: break
	g[nome]=[0,0,0,0]
	print(f"Super, il nuovo discepolo, {nome}, numero {len(g)} si è unito alla schiera.")
	print("Supremo Rabby, vado ad aggiungere i nuovi abbinamenti al tabellone delle partite da giocare.")
	oldpi=len(pi)
	pi=Coppie(g,pi,k,nome)
	print(f"Ecco fatto! Le partite da giocare sono salite da {oldpi} a {len(pi)}.")
	return g,pi
def Modgioc(g,pi,pc):
	'''modifica un giocatore o lo rimuove, aggiornando anche le partite in corso'''
	while True:
		nome=dgt("Certo mia icona venerata, son qui io per raddrizzare quel giocatore che ha osato smarrire il sentiero. Dimmi subito chi è! ",kind="s",smin=1,smax=50)
		nome=nome.title()[:50]
		if nome in g: break
		else:
			print(f"Oh Anima grande, {nome} sembra non essere fra i tuoi seguaci adoranti! Riproviamo")
			ListaG(g)
	print(f"Perfetto, {nome} trovato. Se è un caso disperato, vuoi che lo sopprima immediatamente?\n\t(S)ì, sopprimilo subito oppure un altro tasto per lasciare che continui ad adorarti ")
	s=key("Premi (S) per sopprimere oppure un altro tasto: ")
	if s.lower()=="esc":
		print("Operazione annullata.")
		return g,pi,pc
	if s.lower()[:1]=="s":
		g.pop(nome)
		print("Seccato! Ogni tuo desiderio è un ordine, Maestro.")
		pdr=[]
		for j in list(pi.keys()):
			if nome in pi[j][0] or nome in pi[j][1]:
				pdr.append(j)
		for j in pdr:
			pc[j]=pi.pop(j)
		print(f"Adorabile, ti comunico con gioia che tutte le {len(pdr)} partite con {nome}, sono state spostate nelle completate.")
		recalto, recbasso = RicalcolaRecord(pc)
		return g,pi,pc,recalto,recbasso
	print(f"Uhm... {nome} ha beneficiato della tua mastodontica grazia. Che la correzione abbia inizio!")
	while True:
		s=ninp("Vuoi modificare: (1) i punti, (2) le vittorie, (3) i pareggi o (4) le sconfitte? ",1,4)
		s-=1
		v=ninp(f"{FIELDS[s+1]} attuali di {nome} pari a: {g[nome][s]}\n\tIndicami il valore da sommare, un valore negativo per sottrarre: ")
		g[nome][s]+=v
		print(f"Situazione attuale di {nome}:\n\tpunti {g[nome][0]}, vittorie {g[nome][1]}, pareggi {g[nome][2]}, sconfitte {g[nome][3]}.")
		s=key("Altre modifiche? (S)ì, oppure altro tasto per proseguire: ")
		if s.lower()=="esc":
			print("Operazione annullata.")
			break
		if s.lower()[:1]!="s": break
	# Ricalcolo comunque i record nel caso siano stati modificati i punti manualmente
	# Nota: Modgioc non ha accesso allo storico punti per ricalcolare record basati su modifiche manuali arbitrarie, 
	# ma restituiamo quelli esistenti per coerenza di firma.
	return g,pi,pc,recalto,recbasso # Firma aggiornata per consistenza
def Rifai(pi,pc):
	'''sposta una partita completata nelle incomplete'''
	if len(pc)==0:
		print("Oh mia immacolata beatitudine: non ci sono partite, nella lista delle completate.")
		return pi,pc
	while True:
		pn=ninp("Mio canyon di gratitudine, indicami il numero della partita che desideri spostare nelle incomplete: ",1)
		if pn in pc: break
		else:
			print(f"Oh dolcezza galattica, purtroppo {pn} non è fra le partite già completate. Mi pregio di vergartene una lista:")
			Showmatches(pc)
	print(f"Certo certo, subito, la numero {pn}, ecco, spostata mio padrone sempiterno.")
	pi[pn]=pc.pop(pn)
	return pi,pc
def RicalcolaRecord(pc):
	'''Scansiona tutte le partite completate e ricalcola da zero i record Alto e Basso.'''
	recalto = ['Giocatore sconosciuto','Partita sconosciuta',-99999]
	recbasso = ['Giocatore sconosciuto','Partita sconosciuta',99999]
	for pn, data in pc.items():
		# data struttura: [p1, p2, result, punti]
		# controllo robustezza: se la partita non ha 4 elementi (es. rimossa da Modgioc), la salto
		if len(data) < 4: continue
		p1, p2, res, pt = data[0], data[1], data[2], data[3]
		winner = ""
		if res == '1': winner = p1
		elif res == '2': winner = p2
		elif res == '3': winner = p1 + " Ex Aequo " + p2
		
		match_desc = f"Partita numero ({pn}) {p1} contro {p2}"
		
		# Aggiorno Alto
		if pt > recalto[2]:
			recalto = [winner, match_desc, pt]
		# Aggiorno Basso
		if pt < recbasso[2]:
			recbasso = [winner, match_desc, pt]
	return recalto, recbasso
def Record(rec,nome,pi,pn,pt,alto=True):
	'''aggiorna il record, stampando il nuovo record in base al punteggio'''
	if alto:
		print("Lucore siderale! Abemus nuovo record. Punteggio più alto realizzato da:")
	else:
		print("Lucore siderale! Abemus nuovo record. Punteggio più basso realizzato da:")
	rec[0]=nome
	rec[1]=f"Partita numero ({pn}) {pi[pn][0]} contro {pi[pn][1]}"
	if "Aequo" in rec[0]: pt=pt
	rec[2]=pt
	print(f"{rec[0]} in {rec[1]} col punteggio di {rec[2]}.")
	return rec
def ninp(s='',inf=-99999,sup=99999):
	'''riceve un input numerico con controlli sui limiti'''
	# per semplicità lascio la logica numerica invariata
	while True:
		while True:
			try:
				n=int(input(s))
				b=True
			except ValueError:
				print("Sconfinata galassia di rettitudine, digita solo valori numerici.")
				b=False
			if b: break
		if n>sup:
			print(f"Mia devastante bellezza, purtroppo {n} è più alto di {sup}.")
		elif n<inf:
			print(f"Mio eterno domatore, purtroppo {n} è più basso di {inf}.")
		else: break
	return n
def ConvertiInTempo(Secondi):
	S=Secondi%60
	M=((Secondi-S)%3600)/60
	O=(Secondi-S-M*60)/3600
	return int(O),int(M),int(S)
def Outcla(g,fn,rev,stampa,pc):
	'''stampa la classifica su schermo o su file con ordinamento avanzato (Criterio > Scontro Diretto > Punti Totali > Alfabetico)'''
	if stampa:
		out=open("Dadillo-T.txt","a")
	else:
		out=sys.stdout
	pos=fn
	direction="discendente, " if rev else ""
	flat=[]
	for n,v in g.items():
		flat.append((n,*v))
	
	def compare_players(a, b):
		# a, b sono tuple: (Nome, Punti, Vittorie, Pareggi, Sconfitte)
		# fn è l'indice del criterio primario scelto dall'utente
		
		val_a = a[fn]
		val_b = b[fn]

		# 1. Criterio Primario Scelto dall'Utente
		if val_a != val_b:
			if isinstance(val_a, str): return (val_a > val_b) - (val_a < val_b)
			return (val_a > val_b) - (val_a < val_b)

		# 2. Scontro Diretto (Head-to-Head)
		# Se non stiamo ordinando per nome (fn=0), usiamo lo scontro diretto come tie-breaker
		if fn != 0:
			p1_name = a[0]
			p2_name = b[0]
			score_a = 0
			score_b = 0
			matches_found = 0

			for m in pc.values():
				# m: [Player1, Player2, Result, Points]
				mn1, mn2, mres, mpts = m[0], m[1], m[2], m[3]
				
				# Verifica se è una partita tra A e B
				if (mn1 == p1_name and mn2 == p2_name):
					matches_found += 1
					if mres == '1': score_a += mpts # Vince p1 (A)
					elif mres == '2': score_b += mpts # Vince p2 (B)
					elif mres == '3': # Pareggio
						score_a += mpts
						score_b += mpts
				
				elif (mn1 == p2_name and mn2 == p1_name):
					matches_found += 1
					if mres == '1': score_b += mpts # Vince p1 (B)
					elif mres == '2': score_a += mpts # Vince p2 (A)
					elif mres == '3':
						score_a += mpts
						score_b += mpts
			
			# Se ci sono scontri diretti e i punteggi differiscono
			if matches_found > 0:
				if score_a != score_b:
					return (score_a > score_b) - (score_a < score_b)

		# 3. Punti Totali (Criterio Secondario di default)
		# Se il criterio primario non era già i Punti (indice 1)
		if fn != 1:
			if a[1] != b[1]:
				return (a[1] > b[1]) - (a[1] < b[1])

		# 4. Ordine Alfabetico (Ultima spiaggia per stabilità)
		return (a[0] > b[0]) - (a[0] < b[0])

	print(f"Titolo del torneo: {titolo}",file=out)
	print(creato,file=out)
	if stampa:
		terminato="Torneo concluso in data "+str(time.localtime()[2])+"/"+str(time.localtime()[1])+"/"+str(time.localtime()[0])+" alle ore "+str(time.localtime()[3])+":"+str(time.localtime()[4])+"."
		print(terminato,file=out)
	print(f"Classifica in ordine {direction}per {FIELDS[fn]}",file=out)
	print("Pos, Nome, Punti, Vittorie, Pareggi, Sconfitte",file=out)
	
	# Applicazione dell'ordinamento
	rows = sorted(flat, key=functools.cmp_to_key(compare_players), reverse=rev)

	for idx,row in enumerate(rows):
		print(f"{idx+1}°, {row[0]}, PT{row[1]}, V{row[2]}, P{row[3]}, S{row[4]}.",file=out)
	print("Record punteggio più alto:",file=out)
	print(f"{recalto[0]} in {recalto[1]} col punteggio di {recalto[2]}.",file=out)
	print("Record del punteggio più basso:",file=out)
	print(f"{recbasso[0]} in {recbasso[1]} col punteggio di {recbasso[2]}.",file=out)
	print(f"Report generato da Dadillo versione {VERSIONE}, di Gabriele Battaglia.",file=out)
	if stampa:
		print("-"*79,file=out)
		print("\n",file=out)
		out.close()
	return
ultimo_match=None
ultimo_result=None
def OKPartita(g,pi,pc,recalto,recbasso):
	'''assegna il risultato di una partita, aggiornando statistiche e record; memorizza l'ultima partita per eventuale annullamento'''
	print("Ok, si è conclusa una delle partite. Cerchiamo di capire quale.\nScrivi qui il nome, o parte del nome di uno dei 2 avversari, poi premi invio.")
	cerca=dgt("? ",kind="s")
	Showmatches(pi,cerca)
	while True:
		pn=ninp("Digita il numero della partita a cui vuoi assegnare il risultato: ",1)
		if pn in pi: break
		else:
			print(f"Mio oceano di saggezza, purtroppo {pn} non è fra le partite da completare. Mi pregio di vergartene una lista:")
			Showmatches(pi)
	print("Risultato per la partita numero\n(%d) %s contro %s."%(pn,pi[pn][0],pi[pn][1]))
	while True:
		s=key("Vince (1) "+pi[pn][0]+", (2) "+pi[pn][1]+", oppure (3) pareggio? ")
		if s.lower()=="esc":
			print("Operazione annullata.")
			return g,pi,pc,recalto,recbasso
		if s in ['1','2','3']: break
		else: print("Gulp, mi prostro ai suoi odorosi piedi signore, non capisco il suo volere!")
	if s=='1':
		pt=ninp("Buon per "+pi[pn][0]+", quanti punti ha realizzato? ")
		g[pi[pn][0]][0]+=pt
		g[pi[pn][0]][1]+=1
		g[pi[pn][1]][3]+=1
		if pt>recalto[2]:
			recalto=Record(recalto,pi[pn][0],pi,pn,pt)
		if pt<recbasso[2]:
			recbasso=Record(recbasso,pi[pn][0],pi,pn,pt,False)
	elif s=='2':
		pt=ninp("Buon per "+pi[pn][1]+", quanti punti ha realizzato? ")
		g[pi[pn][1]][0]+=pt
		g[pi[pn][1]][1]+=1
		g[pi[pn][0]][3]+=1
		if pt>recalto[2]:
			recalto=Record(recalto,pi[pn][1],pi,pn,pt)
		if pt<recbasso[2]:
			recbasso=Record(recbasso,pi[pn][1],pi,pn,pt,False)
	elif s=='3':
		pt=ninp("Ah wow, abbiamo un bel pareggio fra "+pi[pn][0]+" e "+pi[pn][1]+"\nPunteggio realizzato? ")
		g[pi[pn][0]][2]+=1
		g[pi[pn][1]][2]+=1
		g[pi[pn][0]][0]+=pt
		g[pi[pn][1]][0]+=pt
		if pt>recalto[2]:
			recalto=Record(recalto,pi[pn][0]+" Ex Aequo "+pi[pn][1],pi,pn,pt)
		if pt<recbasso[2]:
			recbasso=Record(recbasso,pi[pn][0]+" Ex Aequo "+pi[pn][1],pi,pn,pt,False)
	res=[pi[pn][0],pi[pn][1],s,pt]
	pc[pn]=res
	del pi[pn]
	global ultimo_match,ultimo_result
	ultimo_match=pn
	ultimo_result=res
	return g,pi,pc,recalto,recbasso
def CancellaUltimaPartita(g,pi,pc,recalto,recbasso):
	'''annulla l'ultima partita inserita, ripristinando le statistiche e reinserendola nelle incomplete'''
	global ultimo_match,ultimo_result
	if ultimo_match is None or ultimo_match not in pc:
		print("Nessuna partita da annullare.")
		return g,pi,pc,recalto,recbasso
	res=pc[ultimo_match]
	p1,p2,resu,pt=res[0],res[1],res[2],res[3]
	if resu=='1':
		g[p1][0]-=pt
		g[p1][1]-=1
		g[p2][3]-=1
	elif resu=='2':
		g[p2][0]-=pt
		g[p2][1]-=1
		g[p1][3]-=1
	elif resu=='3':
		g[p1][0]-=pt
		g[p2][0]-=pt
		g[p1][2]-=1
		g[p2][2]-=1
	pi[ultimo_match]=[p1,p2]
	del pc[ultimo_match]
	print(f"Partita numero {ultimo_match} annullata. Ora reinserita nelle incomplete.")
	ultimo_match=None
	ultimo_result=None
	recalto, recbasso = RicalcolaRecord(pc)
	return g,pi,pc,recalto,recbasso
def ListaG(l):
	'''stampa la lista dei partecipanti'''
	print("Questa è la lista dei partecipanti al torneo:\n\t"+titolo)
	k=1
	for j in l:
		print("%d. %s: PT%d, V%d, P%d, S%d."%(k,j,l[j][0],l[j][1],l[j][2],l[j][3]))
		k+=1
	print("Record punteggio più alto:")
	print(f"{recalto[0]} in {recalto[1]} col punteggio di {recalto[2]}.")
	print("Record del punteggio più basso:")
	print(f"{recbasso[0]} in {recbasso[1]} col punteggio di {recbasso[2]}.")
	return
def Classifica(g,pc):
	'''stampa la classifica generale dei giocatori'''
	print("Subito mia luminescenza,ecco la lista dei %d valorosi partecipanti al torneo ed i risultati maturati fino ad ora."%len(giocatori))
	print("Ma prima, pietà sua infinita clemenza, devo chiederle se vuole ordinare la classifica per:")
	k=1
	for j in FIELDS:
		print("(%d) %s."%(k,j))
		k+=1
	s=ninp("(1), (2), (3), (4) o (5)? ",1,5)
	s-=1; rev=False; stampa=False
	print("O certo, per "+FIELDS[s]+" mio eroe dal braccio potente.")
	s1=key("Ora mi esponga il suo volere, roboante onnipotente: vuole la classifica inversa? (s)ì, oppure (n)o: ")
	if s1.lower()=="esc":
		print("Operazione annullata.")
		return
	if s1.lower()=="s":
		rev=True
		print("Sublime scelta, sole del mio universo.")
	else: print("Naturalmente, mio splendore, l'avrei scelto anch'io... col suo permesso divino s'intende!")
	s1=key("(s)alva su file, oppure (l)eggi a schermo: ")
	if s1.lower()=="esc":
		print("Operazione annullata.")
		return
	if s1.lower()=='s':
		stampa=True
		print("Ma certo mio tsunami d'amore, sono pronto a marchiare il mio corpo a sangue per te!")
	else: print("Lo dicevo io, mio adorato. Eccola qui in arrivo!")
	Outcla(g,s,rev,stampa,pc)
	return
def Showmatches(l,cerca=""):
	'''stampa la lista delle partite (filtrata se cerca è non vuoto)'''
	if len(l)<1:
		print("Ups, mio signore, questa lista è vuota.")
		return
	elif len(l)<4:
		print("Oh incommensurabile vastità, rimangono meno di 4 partite. Disabilito il filtro.")
		cerca=""
	for j in l:
		s1="("+str(j)+") "+str(l[j][0])+" vs "+str(l[j][1])+"."
		if cerca!="":
			if cerca.lower() in s1.lower(): print(s1)
		else: print(s1)
	return
def ClassificaAvulsa(g,pc):
	'''stampa la classifica avulsa per gruppi di 3 o più giocatori con lo stesso numero di vittorie, calcolando solo i match disputati tra di loro'''
	grp={}
	for player,stats in g.items():
		wins=stats[1]
		grp.setdefault(wins,[]).append(player)
	for wins,players in grp.items():
		if len(players)>=3:
			print(f"Classifica avulsa per i giocatori con {wins} vittorie complessive:")
			internal={}
			for player in players:
				internal[player]=[0,0]  # [vittorie interne, punti interni]
			for m in pc.values():
				p1,p2,res,pts=m[0],m[1],m[2],m[3]
				if p1 in players and p2 in players:
					if res=='1':
						internal[p1][0]+=1
						internal[p1][1]+=pts
					elif res=='2':
						internal[p2][0]+=1
						internal[p2][1]+=pts
					elif res=='3':
						internal[p1][1]+=pts
						internal[p2][1]+=pts
			sorted_pl=sorted(players,key=lambda p:(internal[p][0],internal[p][1]),reverse=True)
			for idx,p in enumerate(sorted_pl):
				print(f"{idx+1}°. {p}: Vittorie interne {internal[p][0]}, Punti interni {internal[p][1]}.")
def Menu():
	'''visualizza il menù'''
	print("\nMia estatica moltitudine di gioia, ecco tutto ciò che posso fare per il mio supremo padrone.\n\tDadillo versione "+VERSIONE+". Tutti i comandi vanno seguiti dalla pressione del tasto invio.")
	print(" - - ( AGT ) - - Aggiungi Giocatore al Torneo;")
	print(" - - ( CLA ) - - Classifica;")
	print(" - - ( LG  ) - - Lista Giocatori;")
	print(" - - ( LPC ) - - Lista Partite Completate;")
	print(" - - ( LPI ) - - Lista Partite incomplete;")
	print(" - - (  M  ) - - visualizza questo Menù;")
	print(" - - ( MSG ) - - Modifica Situazione Giocatore;")
	print(" - - ( OK  ) - - Partita completata!;")
	print(" - - ( SPI ) - - Sposta Partita nelle Incomplete;")
	print(" - - ( CAN ) - - Annulla l'ultima partita;")
	print(" - - ( CLAAV ) - - Classifica Avulsa;")
	print(" - - ( SAV ) - - Salva manualmente;")
	print(" - - (  U  ) - - Uscita dal programma;")
	return
def Immissione():
	'''crea la struttura dati iniziale inserendo i partecipanti'''
	print("Evviva mio amato! Diamo il via ad un nuovo torneo di adorazione per te,\na DiceWorld! Sua vastità, indicami tutti i nomi dei partecipanti. Ogni nome dovrà essere univoco.\nPer concludere batti invio a vuoto.")
	j=1;giocatori={}
	while True:
		nome=dgt("Giocatore "+str(j)+": ",kind="s",smin=0)
		if nome=="":
			break
		nome=nome[:16].title()
		if nome not in giocatori:
			giocatori[nome]=[0,0,0,0]
			j+=1
		else:
			print(f"Santissima entità, {nome} è già stato annoverato fra i tuoi fedeli, scrivi un nome diverso.")
	parinc={};k=1
	parinc=Coppie(giocatori,parinc,k)
	return [giocatori,parinc,{}]
print("Dadillo: DiceWorld Tournament Manager by Gabriele Battaglia\n\tVersione: "+VERSIONE)
print("Oh mio adorato, supremo Maestro e padrone. Grazie per avermi chiamato. Sono qui per servirti, ti prego, sfruttami più che puoi!")
try:
	f=open("Dadillo-T.db","r")
	dati=json.load(f)
	f.close()
	giocatori,dati[1],dati[2],contcom,titolo,creato,recalto,recbasso=dati[0],dati[1],dati[2],dati[3],dati[4],dati[5],dati[6],dati[7]
	# riconversione chiavi numeriche
	parinc=conv_key_int(dati[1])
	parcom=conv_key_int(dati[2])
	print("   Oh quale gaudio! Ho trovato le tue direttive per me. Ottempererò con gioia, mia divinità.")
except:
	print("...File Dadillo-T.db, non trovato\n\t...ne creo immediatamente uno nuovo fiammante per te, o mia entità luminosa!")
	dati=Immissione()
	dati.append(1)
	titolo=dgt("Mia estremitudine immortale, vorresti vergare qui, se ti compiace, il titolo di questo torneo? ",kind="s",smin=1,smax=50)
	titolo=titolo.title()[:50]
	dati.append(titolo)
	creato="Torneo iniziato in data "+str(time.localtime()[2])+"/"+str(time.localtime()[1])+"/"+str(time.localtime()[0])+" alle ore "+str(time.localtime()[3])+":"+str(time.localtime()[4])+"."
	dati.append(creato)
	recalto,recbasso=['Giocatore sconosciuto','Partita sconosciuta',-99999],['Giocatore sconosciuto','Partita sconosciuta',99999]
	dati.append(recalto)
	dati.append(recbasso)
	with open("Dadillo-T.db","w") as f:
		json.dump(dati,f,indent="\t")
	print("\nFile Dadillo-T.db, salvato con successo.")
	giocatori,dati[1],dati[2],contcom=dati[0],dati[1],dati[2],dati[3]
	parinc=conv_key_int(dati[1])
	parcom=conv_key_int(dati[2])
print("Il torneo attivo ha "+str(len(giocatori))+" giocatori, impegnati in "+str(len(parinc)+len(parcom))+" partite.")
print("Barra di avanzamento, torneo completo al %3.1f%%:\n%d completate su %d ancora da giocare, %d  partite totali."%(len(parcom)*100/(len(parinc)+len(parcom)),len(parcom),len(parinc),len(parinc)+len(parcom)))
print("\tSia fatta la tua volontà nel digitare ( M ) seguito da invio, affinché io mi pregi di mostrarti il menù.\n\t\tAmen!")
acccom=['agt','cla','lpc','lpi','lg','m','msg','ok','spi','u','sav','can','claav']
fine=False
while True:
	s=dgt("["+str(contcom)+"] comandi signore: ",kind="s")
	s=s[:3].lower()
	if s in acccom:
		contcom+=1
		if s=="u": break
		elif s=="m": Menu()
		elif s=="lg": ListaG(giocatori)
		elif s=="spi": parinc,parcom=Rifai(parinc,parcom)
		elif s=="agt":
			k_start = max(list(parinc.keys()) + list(parcom.keys()) + [0]) + 1
			giocatori,parinc=Agggioc(giocatori,parinc,k_start)
		elif s=="msg": giocatori,parinc,parcom=Modgioc(giocatori,parinc,parcom)
		elif s=="ok":
			giocatori,parinc,parcom,recalto,recbasso=OKPartita(giocatori,parinc,parcom,recalto,recbasso)
			print("Barra di avanzamento, torneo completo al %3.1f%%:\n%d completate su %d ancora da giocare, %d  partite totali."%(len(parcom)*100/(len(parinc)+len(parcom)),len(parcom),len(parinc),len(parinc)+len(parcom)))
			if len(parinc)==0:
				fine=True
		elif s=="cla": Classifica(giocatori,len(parcom))
		elif s=="lpc":
			print("Lista partite completate")
			Showmatches(parcom)
		elif s=="lpi":
			print("Lista partite incomplete")
			Showmatches(parinc)
		elif s=="sav":
			dati=[giocatori,parinc,parcom,contcom,titolo,creato,recalto,recbasso]
			with open("Dadillo-T.db","w") as f:
				json.dump(dati,f,indent="\t")
			print("Modifiche in File Dadillo-T.db, salvate con successo (manuale).")
		elif s=="can":
			giocatori,parinc,parcom,recalto,recbasso=CancellaUltimaPartita(giocatori,parinc,parcom,recalto,recbasso)
		elif s=="claav":
			ClassificaAvulsa(giocatori,parcom)
	else:
		print("Spiacente mia estrema magnificenza, mi fustigo ma non comprendo il comando.")
	if fine: break
	dati=[giocatori,parinc,parcom,contcom,titolo,creato,recalto,recbasso]
	with open("Dadillo-T.db","w") as f:
		json.dump(dati,f,indent="\t")
print("\nModifiche in File Dadillo-T.db, salvate con successo.")
if fine:
	print("Argh, ma cosa vedono le mie fosche pupille digitali, il Torneo è finito!")
	print("La scorto subito in sala classifica, mio elevatissimo.")
	Classifica(giocatori,parcom)
durata=time.time()-TEMPO
Orologio=ConvertiInTempo(durata)
print("Mi hai schiavizzato soltanto per %2d ore, %2d minuti e %2d secondi."%Orologio)
print("Torna presto a sfruttarmi, mio amato, arrivederci!")
