# coding: utf-8

from django.conf import settings
from django.utils.safestring import mark_safe
from django.shortcuts import render


def changeLog(request, template_name='static/changelog.html'):
    """ Return a list of changes with version <= current version """
    current_version = settings.TAM_VERSION
    changes = []
    prenotazioni = 'prenotazioni' in settings.PLUGGABLE_APPS
    known_changes = [
        ('1.0', '10/10/2009', mark_safe('<b>TAM diventa definitivo.</b>')),
        ('1.0.1', '29/10/2009', mark_safe('''	Gestione dettagliata dei permessi, ogni utente può avere accesso solo a determinate funzioni.
                                                            Per ora sono presenti 3 gruppi:
                                                            <ul>
                                                                <li>UtentePotente: Utenti che posso cambiare anche le vecchie corse.</li>
                                                                <li>UtenteNormale: Utente che può inserire nuove corse e modificare quelle future.</li>
                                                                <li>Tutti gli altri, che possono accedere in sola lettura.</li>
                                                            </ul>''')),
        ('1.0.2', '23/11/2009', mark_safe('''<strong>Gestione utenti</strong>: gli utenti abilitati possono creare e cancellare gli utenti di TaM, modificarne le password (cancellando automaticamente tutte le sessioni aperte) e il gruppo di permessi.<br/>
                                                            Reimpaginata la schermata di login.	Pagina dei cambiamenti e regole.<br/>''')),
        ('1.1', '3/12/2009', mark_safe('''<strong>Log delle operazioni</strong>: pagina per la visione delle operazioni, log nella struttura dati, Signal per le operazioni sui modelli (Viaggi, Clienti, Conducenti, Tratte e prezzi listino).<br/>
                                                        Pagina per il cambio della propria password, disponibile per ogni utente cliccando sul proprio nome in fondo alla pagina.''')),
        ('1.12', '8/1/2010', mark_safe('''Visualizzazione classifiche: riordinati i doppi Venezia e compressi i supplementari.<br/>
                                                        Impostato un limite di 3000 corse per l'esportazione in Excel.''')),
        ('1.13', '13/1/2010', mark_safe('''Aggiunto al Log delle operazioni la possibilità di filtrare in base all'utente che ha eseguito l'operazione<br/>
                                                        Nella maschera dei prezzi delle corse inserite aggiunto un link alla lista di azioni svolte sulla corsa.''')),
        ('1.14', '13/2/2010', mark_safe('''Dietro le quinte: gestiti con Form.Media i Javascript e CSS; migrazioni gestite con South.<br/>
                                                        I privati ora possono avere il flag di fatturabile e pagamento differito.<br/>
                                                        Inserito il flag "Pagamento con carta di credito".<br/>
                                                        Il filtro "Prossime corse" è il predefinito.<br/>
                                                        Richiesta di conferma nella creazione/modifica delle corse se non si è salvato.''')),
        ('1.15', '18/2/2010', mark_safe('''I privati ora si possono creare al volo dalla prima pagina dell'inserimento corse.
                                                        In fondo, nella seconda pagina, si può tornare in fretta per modificarne i dati.''')),
        ('1.16', '3/3/2010', mark_safe('''L'anagrafica dei clienti privati può ora essere cambiata direttamente dalle corse.<br/>
                                                        Le note del privato vengono stampate (con fondo giallo) nella lista delle corse.<br/>
                                                        Il privato, nella lista delle corse è cliccabile per andare all'anagrafica.''')),
        ('1.17', '12/4/2010', mark_safe(
            'Nel log delle modifiche evidenziate le corse inserite postume.')),
        ('1.18', '14/4/2010', mark_safe(
            'Il flag "conto fine mese" ora è disponibile ad ogni tipo di cliente.')),
        ('1.19', '1/6/2010', mark_safe('''Aggiunta la data del doppio nella classifica Doppi.<br/>
                                                        Migrazione a Django 1.2.''')),
        ('1.2', '23/8/2010', mark_safe('''Corretto il conguaglio di corse con casette multiple in caso di conguagli parziali.<br/>
                                                        Aggiunta la pagina delle azioni correttive per i superuser.''')),
        ('1.21', '24/10/2010', mark_safe('''Revisione della maschera strumenti.<br/>
                                                        Il prezzo al chilometro è fatto sul (lordo-autostrada-consorzio)
                                                            anziché solo sul lordo.<br/>''')),
        ('2.0', '1/1/2011', mark_safe('''<strong>Archiviazione e appianamento su un altro DB.</strong><br/>
                                                        Aggiunti i link ai conducenti e passeggeri modificati sul log degli eventi.<br/>
                                                        Passaggio ad un version control system: GIT.<br/>
                                                        Tutte le richieste di login in un middleware per garantire una
                                                            copertura totale delle funzioni non pubbliche.<br/>
                                                        Aggiunto al log gli eventi di login/logout.<br/>
                                                        Semplificato il controllo licenza per togliere la necessità di interrogare il DB.<br/>
                                                        Nelle classifiche mostro i conducenti anche se non hanno mai corso.<br/>
                                                        Visualizzo l'anno delle corse vecchie e sottointendo l'anno corrente<br/>
                                                        Aggiunta una pagina con lo stato dei backup, eventi loggati e rivista un po' tutta la procedura.<br/>
                                                        Ora gli utenti devono avere il permesso di richiedere un backup ed eventualmente di scaricarlo.<br/>
                                                        Migliorata la visualizzazione in Google Chrome.<br/>
                                                        Aggiunti un flag "speciale" ai luoghi per indicare se sono stazioni o aeroporti.
                                                            Alle non abbinate da questi luoghi viene applicato un abbuono fisso di 5 o 10€ in creazione.<br/>
                                                        I messaggi all'utente rimangono fissi a schermo, per essere meglio visualizzati nella lista corse.<br/>''')),
        ('2.1', '3/8/2011', mark_safe('''Le esportazioni in Excel vengono loggate.<br>
                                                        Viene evidenziato il prezzo lordo, corretto il nome del file esportato dai backup e aggiornata la libreria jquery.<br>
                                                        Grossi miglioramenti nelle prestazioni della lista corse e piccoli miglioramenti generali.''')),
        ('3.0b', '7/1/2012', mark_safe('''<b>Fatturazione</b>.<br/>
                                                            Aggiunta la generazione delle fatture da consorzio a cliente, da conducente a cliente e le
                                                            ricevute da alcuni conducenti al cliente.<br/>
                                                            I conducenti ora hanno un flag che indica se possono emettere ricevute.<br>
                                                            <p>
                                                                Cambiamenti alla gestione dei media.<br/>
                                                                Il tasto ESC da ovunque chiede se ci si vuole disconnettere.<br/>
                                                                Aggiunte le note del cliente, visibili nella lista corse.<br/>
                                                            </p>
                                                            Gli utenti normali non possono più inserire corse con data passata.''')),
        ('3.1', '13/2/2012', mark_safe('''Quando parto da un aeroporto tengo conto di mezz'ora in più prima di ritornare.<br/>
                                                            Aggiunto un'opzione ai listini per forzare la fatturazione, per forzare la NON fatturazione o per lasciare l'impostazione del cliente.<br/>
                                                            I punti supplementari ora sono calcolati a quarti a seconda della fascia notturna/mattutina toccata e sono assegnati interamente come notturni o mattutini in base alla prevalenza del supplementare.''')),
        ('3.4', '7/5/2012', mark_safe('''Aggiornamento a Django 1.4 e piccole migliorie varie.<br />
                                                            Gli utenti normali ora possono modificare le note in testata delle fatture.<br />
                                                            Messaggi con nuovo framework distinti tra errori, warning, info... ''')),
        ('3.41', '17/5/2012', mark_safe('''Le ricevute si generano normalmente ma producono due documenti:<br/>
                                                            uno dal consorzio al cliente e uno dal conducente al consorzio.''')),
        ('3.5', '28/5/2012', mark_safe(
            'Log su DB separato per avere maggiore concorrenza in scrittura. Migliorata l\'occupazione su disco.')),
        ('3.6', '4/6/2012', mark_safe('''Separata la gestione dei parametri per rendere le fatturazione e classifiche estraibili.<br/>
                                                        Sessioni cookie-based per caricare meno il DB.''')),
        ('3.7', '1/7/2012', mark_safe('''Rivista la procedura di fatturazione per rendere tutto più dinamico e parametrizzabile.<br>
                                                        Le ricevute ora non sono più generabili, al loro posto vengono create
                                                        delle fatture esenti iva consorzio e conducente.''')),
        ('3.7.4', '31/8/2012', mark_safe(
            'Qualche ottimizzazione alla visualizzazione delle corse, campi data modificabili in testata fatture.')),

        ('3.7.5', '7/9/2012',
         mark_safe('Evidenziati i prezzi a zero nella lista corse.')),
        ('3.7.6', '21/9/2012', mark_safe(
            'Le fatture conducente senza IVA, per i conducenti che non possono emettere senza IVA ora hanno l\'iva')),
        ('3.7.7', '21/9/2012',
         mark_safe('Miglioramenti ai Task per i processi lunghi.')),
        ('3.7.8', '24/9/2012', mark_safe('''Nell'elenco passeggeri privati, ora è possibile vedere
                                                        in quante corse è usato un passeggero e se non è usato in nessuna
                                                        corsa futura, cancellarlo (utenti potenti).''')),
        ('4.0.0', '1/10/2012', mark_safe('''Backup su PostgreSQL più veloce e senza problemi di lock in scrittura.<br/>
                                                        Backup reimplementato con le funzioni native del nuovo db.''')),
        ('4.0.1', '8/10/2012', mark_safe('''Varie correzioni di errori.<br />
                                                        Aggiunto un flag per annullare le corse, in modo da evidenziarle
                                                        mantenendole fuori dalle classifiche e fuori dagli Excel. <br />
                                                        Sfondo dei gruppi di corse con sfondo alternato, per facilitarne la lettura.''')),
        ('4.0.3', '22/10/2012', mark_safe('''Possibilità di generare un pdf di un blocco di fatture selezionate
                                                        dalla visualizzazione fatture.''')),
        ('4.1', '14/2/2012', mark_safe('''Stampa dei listini in PDF.''')),
        ('4.5', '15/12/2012', mark_safe('''<b>Sistema di prenotazioni online</b> gestione clienti prenotazioni multiple,
                                                        inserimento e modifiche prenotazioni con notifiche via email e inserimento in TAM.
                                                    ''')) if prenotazioni else "",
        ('4.6', '14/1/2013',
         'File allegato alle prenotazioni.') if prenotazioni else "",
        ('4.7', '19/2/2013',
         'Gli utenti delle prenotazioni vedono le corse inserite dal consorzio oltre alle prenotazioni.') if prenotazioni else "",
        ('4.8', '24/2/2013',
         'Logo personalizzato nella pagina di login, più filtri sulla visualizzazione.'),
        ('4.9', '24/2/2013',
         'Seleziona rapida dei 2 mesi precedenti nella visualizzazione fatture.'),
        ('5.0', '6/3/2013',
         'Supporto a timezone differenti sul server. Fix e miglioramenti vari.'),
        (
            '5.1', '29/3/2013',
            'Memorizza quando nelle prenotazioni è stato inviato un allegato.' if prenotazioni else ""),
        ('5.2', '9/5/2013',
         'Possibilità di cancellare un cliente, dopo aver cancellato le sue corse.'),
        ('5.3', '10/5/2013',
         'Forzo la selezione di tutte le corse quando clicco su un\'abbinata.'),
        ('5.5', '1/4/2013',
         mark_safe(
             '<b>Bacheca notizie in realtime.</b>')) if 'board' in settings.PLUGGABLE_APPS else "",
        ('5.6', '18/6/2013', mark_safe(
            '<b>Coda presenze.</b>')) if 'codapresenze' in settings.PLUGGABLE_APPS else "",
        ('5.7', '24/6/2013', mark_safe(
            'Gli utenti potenti ora possono gestire la coda di tutti.')) if 'codapresenze' in settings.PLUGGABLE_APPS else "",
        ('5.9', '10/5/2013',
         'Cambiata la gestione degli assets per alleggerirne il peso e farne il versioning.'),
        ('5.95', '29/9/2013',
         'Ordinamento utenti, unicità case-insensitive dei passeggeri e sistemazioni varie.'),
        ('5.96', '27/12/2013',
         'Aggiornamenti vari e ultima versione del framework.'),
        ('5.97', '16/2/2014', 'Deployment rivoluzionato.'),
        ('5.98', '8/3/2014',
         'Filtro prenotazioni per data da-a e cambio stile date selectors nelle prenotazioni.'),
        ('5.99', '14/3/2014',
         'È possibile inibire la cancellazione delle corse. '
         'Cambio sui costi della sosta nei collettivi in partenza.'),
        ('5.991', '4/4/2014',
         'Ottimizzazioni sul calcolo delle classifiche e sulle select dinamiche.'),
        ('6.0', '12/4/2014', mark_safe('<b>Gestione presenze.</b> ' +
                                       "Le classifiche viaggio tengono conto di ferie/permessi e viaggi contemporanei")
         ) if 'calendariopresenze' in settings.PLUGGABLE_APPS else "",
        ('6.0', '30/4/2014',
         "Schermata prenotazioni e login multilingua.") if 'prenotazioni' in settings.PLUGGABLE_APPS else "",
        ('6.1', '11/7/2014',
         "Conservazione sicura degli allegati alle prenotazioni.") if 'prenotazioni' in settings.PLUGGABLE_APPS else "",
        ('6.11', '22/7/2014',
         "Fix board per device touch.") if 'board' in settings.PLUGGABLE_APPS else "",
        ('6.12', '15/8/2014',
         "Archiviazione con data personalizzabile e aggiornamenti vari."),
        ('6.15', '19/8/2014', "Cambiamenti al layout, mobile friendly."),
        ('6.16', '6/10/2014', "Nascondo i clienti inattivi."),
        ('6.17', '2/11/2014', "CSRF e clickjacking protections."),
        ('6.18', '2/11/2014', "Django 1.7 e varie migliorie."),
        ('6.19', '9/2/2015', "Maggior dettaglio nel log della fatturazione."),
        ('6.20', '28/2/2015',
         "Presenze resettabili custom.") if 'calendariopresenze' in settings.PLUGGABLE_APPS else "",
        ('6.30', '10/4/2015',
         "Visualizzazione allegati prenotazioni.") if 'prenotazioni' in settings.PLUGGABLE_APPS else "",
        ('6.38', '27/6/2015', "Django 1.8 e pulizia."),
        ('6.40', '26/7/2015', "Imposta di bollo so se importo >= minimo."),
        ('6.45', '7/11/2015', "Alleggerita la procedura di backup, ora piu' veloce."),
        ('6.46', '16/12/2015', "Fix al minimo per imposta di bollo"),
        ('6.47', '13/2/2016', "BUS filters and framework updates"),
        ('6.5', '23/2/2016', "Report corse"),
        ('6.6', '16/3/2016', "Cambio di backend per l'invio di mail."),
        ('6.7', '1/5/2016',
         "Controllo sessioni singole") if settings.FORCE_SINGLE_DEVICE_SESSION else "",
        ('6.72', '5/8/2016', "Webhooks per essere notificati degli errori di consegna delle email"),
        ('6.72', '14/8/2016', "Preavviso per prenotazioni regolabile in base all'orario"),

    ]
    # ('', '', mark_safe('''''')),
    for version in known_changes[::-1]:
        if not version: continue  # version può essere vuoto... salto la riga
        if version[0] and version[0] <= current_version:
            changes.append(version)
    return render(request, template_name, {'changes': changes})
