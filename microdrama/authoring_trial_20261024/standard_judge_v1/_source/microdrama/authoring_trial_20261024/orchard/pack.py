"""A notebook, a frost trial, and a finite night's work."""
from microdrama.engine import World, Memeplex, Microdrama, StoryError

TITLE = 'The White Ribbons'


def build_world(config):
    assert set(config) == {'access', 'cooperate', 'distraction'}
    entities = {x: {'kind': kind} for x, kind in [('valley','group'),('mara','character'),('ivo','character'),('notebook','book'),('fork','tool'),('trial','plant'),('rows','plants')]}
    s = {x+'.location':'orchard' for x in entities}
    s.update({'valley.ended':False,'valley.outcome':'','valley.stage':0,'valley.frost':True,
        'valley.trial_cold':1,'valley.night_cold':1,
        'mara.distracted':config['distraction'],'mara.belief':'bees','mara.observed_cause':'unknown',
        'ivo.willing':config['cooperate'],'notebook.accessible':config['access'],
        'fork.owner':'ivo','fork.user':'ivo','fork.returned':False,
        'trial.cause':'frost','trial.tested':False,'trial.protected':0,
        'trial.air_gap':False,'trial.anchored':False,'trial.retains_warmth':False,'trial.resistance':0,
        'rows.air_gap':False,'rows.anchored':False,'rows.resistance':0,
        'rows.protected':0,'rows.surviving':0,'rows.total':6})
    content = Memeplex.atom('air_gap') + Memeplex.atom('anchor_edges')
    for carrier in ('notebook','mara'):
        for name, value in content.terms:
            s[carrier+'.meme.'+name] = value if carrier == 'notebook' else 0.0
    return World(entities, ('orchard','shed'), s, validate)


def validate(s):
    if s['valley.frost'] is not True: raise StoryError('This story has an overnight frost as a fixed premise')
    if not (1 <= s['valley.trial_cold'] <= 3 and 1 <= s['valley.night_cold'] <= 3): raise StoryError('Cold severity is a bounded physical condition')
    if s['trial.cause'] != 'frost': raise StoryError('Belief cannot rewrite frost injury')
    if s['fork.owner'] != 'ivo': raise StoryError('A loan preserves ownership')
    if s['trial.protected'] and not (s['trial.air_gap'] and s['trial.anchored']): raise StoryError('The trial needs a working physical shelter')
    if s['rows.protected'] and not (s['rows.air_gap'] and s['rows.anchored']): raise StoryError('Protected rows need roofs and anchors')
    if s['fork.user'] not in ('ivo','mara'): raise StoryError('Tool has a real user')
    if not 0 <= s['rows.surviving'] <= s['rows.protected'] <= 6: raise StoryError('Protection is bounded')
    if s['rows.protected'] and (not s['trial.retains_warmth'] or s['fork.user'] != 'mara') and not s['valley.ended']:
        raise StoryError('Working protection needs a tested method and the borrowed fork')
    if s['rows.protected'] > 2 and not s['ivo.willing']: raise StoryError('Six rows require two workers')


def shelter(tx, learner, target, count):
    """Same physical practice, bound to a trial branch or the orchard rows."""
    tx.require(tx.get(learner+'.location') == tx.get(target+'.location'), 'Worker can reach the shelter')
    tx.set(target+'.air_gap', tx.get(learner+'.meme.air_gap') >= .8)
    tx.set(target+'.anchored', tx.get(learner+'.meme.anchor_edges') >= .8)
    skilled = tx.get(target+'.air_gap') and tx.get(target+'.anchored')
    tx.set(target+'.protected', count if skilled else 0)
    tx.set(target+'.resistance', 2 if skilled else 0)
    if target == 'trial':
        tx.set('trial.retains_warmth', tx.get('trial.resistance') >= tx.get('valley.trial_cold'))
    if target == 'trial': tx.set('trial.tested', True)


def perform(stage):
    def run(world, params):
        def action(tx):
            tx.require(tx.get('valley.stage') == stage, 'Encounters follow the night')
            if stage == 0:
                tx.get('valley.frost'); tx.get('mara.belief')
            elif stage == 1:
                tx.observe('mara','trial','trial.cause','mara.observed_cause')
                tx.set('mara.belief',tx.get('mara.observed_cause'))
            elif stage == 2:
                if tx.get('notebook.accessible'):
                    tx.absorb('notebook','mara',divisor=2 if tx.get('mara.distracted') else 1)
            elif stage == 3:
                shelter(tx,'mara','trial',1)
            elif stage == 4:
                tx.set('fork.user','mara')
                tx.get('ivo.willing')
            elif stage == 5:
                tx.require(tx.get('fork.user') == 'mara','Mara has temporary use of the fork')
                if tx.get('trial.retains_warmth'):
                    shelter(tx,'mara','rows',6 if tx.get('ivo.willing') else 2)
            elif stage == 6:
                cold = tx.get('valley.night_cold') if tx.get('valley.frost') else 0
                survives = tx.get('rows.resistance') >= cold
                tx.set('rows.surviving',tx.get('rows.protected') if survives else 0)
                n = tx.get('rows.surviving')
                tx.set('valley.outcome', 'whole orchard' if n == 6 else 'two rows' if n else 'lost blossoms')
            elif stage == 7:
                tx.set('fork.user','ivo'); tx.set('fork.returned',True); tx.set('valley.ended',True)
            tx.set('valley.stage',stage+1)
        world.act('night'+str(stage), ['warning','inspection','reading','small trial','loan','sheltering','dawn','return'][stage], ['mara','ivo'] if stage in (0,4,5,7) else ['mara'],action)
    return run


def dramas():
    return tuple(Microdrama('night'+str(i),lambda s,i=i:s['valley.stage']==i,perform(i),practice='shelter' if i in (3,5) else 'encounter') for i in range(8))


def render(ep):
    s=ep.after; stage=int(ep.id[5:]); reveals=[]
    if stage==0:
        text='''Mara had tied white ribbons to the six orchard rows that morning. Each ribbon marked fruit promised to a different kitchen, including the kitchen where Ivo cooked for the school. Now the weather bell was ringing for an overnight frost. There were blankets in the shed, but the branches were too low to drape carelessly. “The bees ruined the early blossoms,” Mara said, repeating the explanation she had heard all week. “Perhaps covering these will keep them out.” Ivo looked at the darkening sky. They had a few hours, and no spare spring.'''
        reveals=['valley.frost','mara.belief','rows.total']
    elif stage==1:
        text='''At the end of the first row, Mara bent over the damaged branch they had kept for comparison. The unopened buds were black inside; even flowers under a fine mesh bag had the same injury. A dated frost marker beside the branch matched the night of the damage. Bees had never entered that bag. “Cold,” she said at last. “We have been blaming the thing that brings us fruit.” The discovery did not mend a single blossom. It did change what she meant to shut out tonight.'''
        reveals=['trial.cause','mara.observed_cause','mara.belief']
    elif stage==2:
        if s['notebook.accessible']:
            text='''Ivo brought out his father's field notebook, its swollen leather cover held shut with string. On the orchard bench, Mara opened a page showing cloth raised clear of the flowers and edges anchored against the ground. The words and drawing belonged together: a pocket of still air, not a wet blanket pressing on petals.'''
            text += (''' But the bell kept pulling her eyes toward the road, where she expected a late delivery. She caught only half the method, remembering the cloth more clearly than its spacing and anchors.''' if s['mara.distracted'] else ''' She traced the drawing with a dirty finger, then said both instructions aloud. Ivo waited while she checked the page once more. This time she had attended to the whole method.''')
        else:
            text='''Ivo found his father's field notebook inside the jammed glass cabinet beside the orchard bench. Mara could see the leather cover but could not reach the pages. They tried lifting the warped door; the frame held. “There was a drawing about frost,” Ivo said, unable to remember its details. The notebook stayed behind the glass, carrying instructions neither of them could use. Outside, Mara spread a blanket on the bench and considered what she could test before risking the six rows.'''
        reveals=['notebook.accessible','mara.meme.air_gap','mara.meme.anchor_edges']
    elif stage==3:
        text=('''Mara made a shelter over the comparison branch: two short sticks, a roof of cloth, and stones closing the edges. She slid her hand underneath to check that no petal touched the fabric. A little cup of warm water remained warmer under that pocket than its twin on the bench. The small trial held its warmth. “That is something we can build,” she said. For the first time that evening, the blankets looked like a method instead of a heap of hopeful laundry.''' if s['trial.retains_warmth'] else '''Mara tried the blanket on the comparison branch. It sagged against the flowers, and a loose edge lifted every time the wind crossed the bench. The little cup beneath it cooled as quickly as its uncovered twin. She took the blanket off before its damp weight bent the twig. “That isn't a shelter yet,” she admitted. The failed trial spared the orchard a false promise, but it had consumed the last margin of light. They still had cloth, and still lacked a working way to use it.''')
        if s['trial.protected'] and not s['trial.retains_warmth']:
            text = 'Mara raised the cloth clear of the comparison branch and anchored every edge. But the cold had already sharpened beyond what this thin roof could resist. The covered cup chilled despite the sound construction. She checked the gap and stones again; nothing had slipped. “We built it properly,” she said, “but it is not enough for this cold.” The failed trial left her without a working shelter to repeat before darkness. Knowledge had put a roof in her hands; it could not make the cloth thicker.'
        reveals=['trial.tested','trial.protected','trial.air_gap','trial.anchored','trial.retains_warmth','trial.resistance','valley.trial_cold']
    elif stage==4:
        text='''Ivo held out his long fork, the one with his initials burned into the handle. It could lift cloth above the branches without tearing it. “Borrow it until morning,” he said. Mara took it carefully; the tool was still his, even while her hands controlled it. '''
        text+=('''Then he rolled up his sleeves. “You raise the roof; I'll carry stones and close the sides.” They would be able to move along the rows together, with neither leaving a half-finished shelter behind.''' if s['ivo.willing'] else '''Then he shouldered the empty school baskets. The kitchen roof had sprung a leak, and he had to go. Mara would have to lift the cloth and fetch every stone herself. The loan helped, but it could not give her another pair of hands.''')
        reveals=['fork.owner','fork.user','ivo.willing']
    elif stage==5:
        n=s['rows.protected']
        text={6:'''Working together, they roofed all six rows. Mara lifted each sheet with the fork while Ivo planted supports and carried stones along the hem. They checked for hanging corners before moving on. At the last white ribbon, he held the cloth while she crawled underneath to free a snagged shoot. It was slow, awkward work, nothing like merely knowing a drawing. When they stood up, six low roofs lay along the orchard, with living flowers clear of their undersides.''',2:'''Alone, Mara finished two rows before the soil began to whiten. Every sheet meant a journey for supports, another for stones, and a careful lift with Ivo's fork. She checked those two shelters instead of beginning a third she could not finish. Four white ribbons still fluttered over exposed branches. She put down the last stone with shaking fingers. Saving only part of the promised fruit hurt, but leaving an unfinished roof would have made that promise smaller still.''',0:'''Mara carried the fork between the rows, then stopped. The bench trial had given her no working shelter to repeat. Raising a sheet for a moment did not keep it raised through a windy night. She folded the blankets beside the gate instead of loading the blossoms with wet cloth. Ivo's tool lay across the folded heap, useful and insufficient. Six white ribbons moved freely above six exposed rows as the first frost silvered the latch.'''}[n]
        if not n and s['trial.protected'] and not s['trial.retains_warmth']:
            text = 'Mara carried the fork between the rows, then stopped. The trial roof had stood properly, but the cold had beaten its thin cloth. Making six more roofs from the same material would not give them greater resistance. She folded the blankets beside the gate while Ivo checked the empty supports. They had a sound method and too little insulation, with no time to fetch heavier covers. Six white ribbons moved above the exposed rows as frost silvered the latch.'
        reveals=['rows.protected']
    elif stage==6:
        n=s['rows.surviving']
        text=f'''At sunrise Mara returned to the ribbons. {'Under all six roofs the flowers remained pale and firm. The promised fruit still had a chance on every row.' if n==6 else 'Beneath the two finished roofs the flowers remained firm; on the other four rows their centers had blackened.' if n==2 else 'Every exposed row held black-centered flowers. No living blossoms remained among the six marked rows.'} She counted carefully: {['no','one','two','three','four','five','six'][n]} rows had surviving blossoms. There was no quarrel left to have with the bees. Cold had done this, and the night's work had determined how much of it the orchard could withstand.'''
        if not n and s['rows.protected']:
            text = 'At sunrise Mara lifted the first shelter and found black centers beneath its undamaged roof. The overnight cold had grown more severe than the bench trial: even the correctly raised and anchored cloth could not resist it. She checked every covered row. All six marked rows had lost their blossoms, including the ones they had sheltered. The roofs still stood, and that made the loss harder to dismiss. Mara laid her palm on a support. Their work had been real; the cold had exceeded what their materials could bear.'
        reveals=['rows.surviving','valley.outcome','valley.night_cold','rows.resistance']
    else:
        text='''Mara wiped the fork's handle and returned it to Ivo. His initials emerged from beneath the soil. '''
        text+=('''Together they untied the white ribbons from the sheltered rows. Ivo folded one into his pocket for the school kitchen; its clean stripe shone against his muddy sleeve.''' if s['rows.surviving']==6 else '''She retied two ribbons beneath the surviving flowers and folded the other four into her coat. The two bright marks stayed visible from the gate.''' if s['rows.surviving']==2 else '''She gathered all six white ribbons and laid them beside the shut notebook. Beyond the bench, a bee landed on an unmarked weed in bloom. Mara left it undisturbed.''')
        reveals=['fork.user','fork.returned','fork.owner']
    return [{'text':text,'evidence':ep.event_ids,'reveals':reveals}]


def questions(world,episodes):
    def q(stage,question,answer,keys):
        ep=episodes[stage]
        return {'question':question,'answer':answer,'facts':[{'event':ep.event_ids[-1],'key':k,'value':ep.after[k]} for k in keys]}
    s=world.state;n=s['rows.surviving']
    return [q(0,'What threatened the promised orchard fruit?','An overnight frost threatened the blossoms on six marked rows. Mara wanted to preserve the fruit already promised to the community kitchens.',['valley.frost','rows.total']),
    q(1,'Why did Mara stop blaming bees?','The comparison branch showed frost injury even inside its mesh bag. Mara changed her belief to cold damage after inspecting that evidence.',['trial.cause','mara.belief']),
    q(2,'Could Mara learn the complete shelter method from the notebook?',('Mara read the accessible notebook and attended to both parts of its method. She learned to leave an air gap and anchor the edges.' if s['notebook.accessible'] and not s['mara.distracted'] else 'Mara reached the notebook, but her divided attention left her with only half the method. The cloth was more memorable to her than its spacing and anchors.' if s['notebook.accessible'] else 'Mara could not read the notebook because it was trapped inside the jammed cabinet. Seeing its cover conveyed none of the instructions on its pages.'),['notebook.accessible','mara.meme.air_gap','mara.meme.anchor_edges']),
    q(3,'What did the small shelter trial establish?',('The trial held warmth beneath cloth raised clear of the branch and anchored at its edges. It gave Mara a working method she could repeat on the orchard rows.' if s['trial.retains_warmth'] else 'The trial had sound construction, but the cold exceeded the shelter resistance. Mara had no effective shelter to repeat before nightfall.' if s['trial.protected'] else 'The trial failed because the cloth sagged and its loose edge admitted wind. Mara had no working shelter to repeat before the light was gone.'),['trial.tested','trial.protected']),
    q(4,'Who owned the fork while Mara used it?','Ivo owned the fork throughout the loan, although Mara held temporary use of it. He asked for its return in the morning.',['fork.owner','fork.user']),
    q(6,'How much of the orchard survived the frost?',('All six marked rows retained living blossoms after the frost. ' if n == 6 else 'Two of the six marked rows retained living blossoms after the frost. ' if n == 2 else 'No marked rows retained living blossoms after the frost. ')+('Every row was protected by the shelters the two workers completed.' if n==6 else 'Mara completed two shelters alone, while four exposed rows lost their blossoms.' if n==2 else 'Even the finished shelters could not resist the more severe overnight cold.' if s['rows.protected'] else 'The failed trial left all six rows exposed to the overnight cold.'),['rows.surviving','valley.outcome']),
    q(7,'What became of the borrowed tool?','Mara cleaned the handle and returned the fork to Ivo in the morning. His initials were visible again beneath the removed soil.',['fork.user','fork.returned','fork.owner'])]
