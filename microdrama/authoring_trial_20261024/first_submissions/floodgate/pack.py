"""The mill's cause, accusation, instruction, and repair occupy separate carriers."""
from microdrama.engine import World, Memeplex, Microdrama

TITLE = 'The Weight Beneath the Water'


def build_world(config):
    assert set(config) == {'access', 'cooperate', 'distraction'}
    entities = {x: {'kind': k} for x, k in [('valley','group'),('ida','character'),('ren','character'),('osk','character'),('diagram','book'),('gate','object'),('sluice','object'),('grain','object'),('lever','object')]}
    state = {x+'.location':'mill' for x in entities}
    state.update({'valley.ended':False,'valley.outcome':'','valley.stage':0,'valley.blamed_ren':True,'valley.water':3,'diagram.accessible':config['access'],'ida.distracted':config['distraction'],'osk.willing':config['cooperate'],'gate.jammed':True,'gate.pin_bent':True,'gate.tested':False,'gate.open':False,'sluice.jammed':True,'sluice.tested':False,'sluice.open':False,'grain.dry':True,'grain.sacks':40,'lever.owner':'osk','lever.user':'osk','ren.can_lift':False,'ida.saw_pin':False,'ida.applied':False,'osk.helped':False})
    for x in ('diagram','ida','ren'):
        for term in ('lift','brace'):
            state[x+'.meme.'+term] = 0.0
    content = Memeplex.atom('lift') + Memeplex.atom('brace')
    for term, magnitude in content.terms:
        state['diagram.meme.'+term] = magnitude
    def validate(s):
        assert s['gate.pin_bent'] is True, 'Opening does not magically straighten the bent pin'
        assert s['lever.owner'] == 'osk', 'Borrowing preserves ownership'
        assert not s['gate.open'] or (s['ida.applied'] and s['osk.helped'] and s['ida.meme.brace'] >= 1), 'Real repair needs applied instructions and a helper'
        assert 0 <= s['grain.sacks'] <= 40
        assert s['grain.dry'] == (s['grain.sacks'] == 40)
        assert s['valley.water'] in (0,3,5)
    return World(entities, ('mill',), state, validate)


def practice(world, actor, target, drama):
    """A portable supported-lift trial; target and learner are bound explicitly."""
    def run(t):
        t.require(t.get(actor+'.location') == t.get(target+'.location'), 'Learner reaches the mechanism')
        t.require(t.get(actor+'.meme.lift') >= 1, 'Learner knows the full lifting instruction')
        t.require(not t.get(target+'.tested'), 'This mechanism has not been tested')
        if target == 'gate':
            t.require(not t.get('ren.can_lift'), 'Ren cannot replace the heavy-lift helper')
        t.set(target+'.tested', True)
        if target == 'sluice':
            t.set(target+'.jammed', False)
            t.set(target+'.open', True)
        else:
            t.set('ida.applied', True)
    world.act(drama, 'supported lift trial', [actor], run)


def encounter(n):
    def perform(w, params):
        name = ('arrival','accusation','diagram','small_trial','inspection','repair','ending')[n]
        if n == 3 and w.state['ida.meme.lift'] >= 1:
            practice(w, 'ida', 'sluice', name)
        if n == 5 and w.state['ida.meme.brace'] >= 1:
            practice(w, 'ida', 'gate', name)
        def mutate(t):
            if n == 1:
                t.set('lever.user','ida')
            elif n == 2:
                if t.get('diagram.accessible'):
                    t.absorb('diagram','ida',divisor=2 if t.get('ida.distracted') else 1)
            elif n == 4:
                t.observe('ida','gate','gate.pin_bent','ida.saw_pin')
                t.set('valley.blamed_ren',False)
            elif n == 5:
                if t.get('ida.applied') and t.get('osk.willing'):
                    t.set('osk.helped',True)
                    t.set('gate.jammed',False)
                    t.set('gate.open',True)
                    t.set('valley.water',0)
            elif n == 6:
                if t.get('gate.open'):
                    t.set('valley.outcome','grain_saved')
                else:
                    t.set('grain.sacks',24)
                    t.set('grain.dry',False)
                    t.set('valley.water',5)
                    t.set('valley.outcome','grain_lost')
                t.set('lever.user','osk')
                t.set('valley.ended',True)
            t.set('valley.stage',n+1)
        w.act(name,'encounter', ['ida','ren','osk'],mutate)
    return perform


def dramas():
    return tuple(Microdrama(name,lambda s,n=n:s['valley.stage']==n,encounter(n),practice='supported_lift' if n in (3,5) else 'encounter') for n,name in enumerate(('arrival','accusation','diagram','small_trial','inspection','repair','ending')))


def render(ep):
    s=ep.after
    paragraphs={
    'arrival': "By breakfast the mill pond had swallowed the bottom step of the grain store. Ida counted forty sacks through the open door; each represented a family's winter bread. The gate should have released the pond into the empty meadow, but its wheel would not turn. Ren, who had arrived in the valley only last week, stood beside it with wet boots. His bandaged wrist could not lift a heavy load, but he wanted to drag the sacks upstairs before the water reached them.",
    'accusation': "Osk planted his long iron lever against the wall. 'We never had this trouble before you came,' he told Ren. Ida disliked how easily the words crossed the yard. She asked to borrow the lever and Osk handed it over, though it remained his tool. Ren took his hands from the wheel. With no one touching it, water continued to press against the gate; the accusation had changed the company in the yard, but had changed nothing beneath the pond.",
    'diagram': ("Ida opened the maintenance diagram beside the wheel. Its two drawings showed a small upward lift before a brace could slide beneath the gate's weight. " + ("She followed both lines with her finger, shutting out the calls from the store. By the time she closed the cover, she could repeat both steps without looking." if not s['ida.distracted'] else "A shout about the sacks pulled her eyes away halfway through each drawing. She caught pieces of the instructions, but neither complete movement; the little arrows blurred together when she tried to recall them.")) if s['diagram.accessible'] else "The maintenance diagram lay inside a glass case beside the wheel, its cover closed. The swollen latch would not lift. Ida could see the book but could not reach a single instruction. Ren offered to break the glass; she looked at the baskets of grain beneath the case and shook her head. They still had the lever, but a tool did not tell them where to put its weight. Water tapped softly against the next step.",
    'small_trial': "Before risking the heavy gate, Ida knelt at the little sluice that fed the mill's washing trough. " + ("She lifted its jammed plate a finger's width, then slipped a stone underneath. The plate came free and the trough filled. Ren watched the stone hold it up. This was a modest success, but now the marks on the page had become a movement Ida's hands could recognize." if s['sluice.open'] else "She set the lever down beside its jammed plate, unable to choose a safe first movement. She left the plate closed. Ren crouched with her, waiting for an instruction she could not honestly give. The untouched trough stayed dry; wishing she understood the gate had not released even this small stream."),
    'inspection': "Ren lay flat on the walkway and held Ida's sleeve while she reached beneath the gate housing. She brought up a bent retaining pin, still fixed at one end, with a bright scrape where it caught the runner. Osk bent down to look. 'That was worn before he arrived,' Ida said. Osk withdrew his accusation aloud. Ren was cleared, but the bent pin still caught the runner. Their new agreement had not repaired the iron.",
    'repair': ("Ida placed Osk's lever beneath the runner and repeated the lift she had practiced. " + ("This time Osk took the weight while she pushed a block into the gap. Together they eased the runner past the bent pin. The gate rose, and water rushed toward the meadow. Ren stood back from the torrent, grinning; the pin remained crooked, but it could no longer hold the gate shut." if s['osk.helped'] else "The heavy runner began to rise, then dragged her arms down. Osk refused to hold it for her. She lowered it carefully rather than trap her hand under the weight. Knowing the sequence had brought her to the right place, but she could not be both lifter and brace at once. The gate stayed shut.")) if s['ida.applied'] else "Ida and Ren carried the lever to the great gate. Neither could identify a safe sequence of lifting and bracing, and Ida would not ask Osk to put his hands under an unsupported runner. They laid the tool down and turned toward the store instead. An extra pair of hands could not supply the missing instructions. The bent pin held fast while the first thin stream crossed the grain store's threshold.",
    'ending': ("By evening all forty sacks stood dry in the store. Ida returned the lever to Osk, and Ren chalked a warning beside the bent pin so tomorrow's repairer would find it. No one called him the cause of the flood again. Across the meadow the released water shone between the grass stems. In the quiet store, Ren sat on the bottom step tying a broken sack cord; this time the step was above water." if s['grain.dry'] else "By evening they had carried twenty-four dry sacks upstairs. Sixteen lay spoiled below, their seams dark in the water. Ida returned Osk's lever and set a chalk mark where the bent pin needed repair. Ren sat with the others dividing the saved grain; no one blamed him now, but no apology could replace the lost bread. Below their feet, the flooded bottom step disappeared whenever the water stirred. The gate would need another attempt before morning.")}
    reveals = {'arrival':['grain.sacks','gate.jammed','ren.can_lift'], 'accusation':['lever.owner','lever.user','valley.blamed_ren'], 'diagram':['diagram.accessible','ida.distracted','ida.meme.lift','ida.meme.brace'], 'small_trial':['sluice.open','sluice.tested'], 'inspection':['gate.pin_bent','ida.saw_pin','valley.blamed_ren'], 'repair':['gate.open','gate.jammed','osk.helped','ida.applied'], 'ending':['grain.sacks','grain.dry','lever.user','gate.pin_bent']}
    return [{'text':paragraphs[ep.id],'evidence':ep.event_ids,'reveals':reveals[ep.id]}]


def questions(world, episodes):
    eps={e.id:e for e in episodes}
    data=[('arrival','grain.sacks','What was Ida trying to protect?','Ida wanted to protect forty sacks of grain in the store. Those sacks represented the families’ winter bread.'),('accusation','lever.owner','Whose lever did Ida borrow?','The long iron lever belonged to Osk, who handed it to Ida. Borrowing the tool left its ownership with him.'),('inspection','gate.pin_bent','What physically stopped the gate?','A bent retaining pin caught the runner beneath the gate housing. Clearing Ren’s name did not straighten that piece of iron.'),('inspection','valley.blamed_ren','How did the accusation change?','Osk withdrew his accusation after Ida showed him the bent pin. Ren was cleared while the mechanical obstruction still remained.'),('small_trial','sluice.open','What happened at the small sluice?', 'Ida freed the little sluice using a lift and a stone brace. Water then entered the washing trough.' if eps['small_trial'].after['sluice.open'] else 'Ida could not choose a safe first movement at the little sluice. She left its plate closed and the washing trough stayed dry.'),('ending','grain.sacks','How much grain remained dry at the end?', 'All forty sacks remained dry after the gate released the pond. Ren could sit on the bottom step above the water.' if world.state['grain.dry'] else 'Twenty-four sacks remained dry after the others were carried upstairs. Sixteen spoiled sacks lay below them in the floodwater.')]
    return [{'question':q,'answer':a,'facts':[{'event':eps[e].event_ids[-1],'key':k,'value':eps[e].after[k]}]} for e,k,q,a in data]
