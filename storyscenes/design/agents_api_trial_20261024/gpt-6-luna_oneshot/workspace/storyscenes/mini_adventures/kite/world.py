"""Offline, bounded kite adventure. Run: python -m storyscenes.mini_adventures.kite.world"""
from __future__ import annotations
from copy import deepcopy
from dataclasses import asdict, dataclass
import argparse, random, re
from storyscenes.runtime import StoryError
from storyscenes.mini_adventures.local_play import LocalPlay

@dataclass(frozen=True, kw_only=True)
class Parameters:
    wind: int = 2                 # 0 calm, 1 gentle, 2 gusty
    reel_sound: bool = False      # whether borrowed line is sound
    shy: bool = True              # neighbour needs a low-pressure invitation
    spare_line: bool = True       # lender has a safe replacement
    name: str = "Mara"
    def __post_init__(self):
        if type(self.wind) is not int or self.wind not in range(3): raise ValueError('wind must be 0, 1, or 2')
        for k in ('reel_sound','shy','spare_line'):
            if type(getattr(self,k)) is not bool: raise ValueError(f'{k} must be bool')
        if not isinstance(self.name,str) or not re.fullmatch(r"[A-Za-z][A-Za-z'-]{0,19}",self.name): raise ValueError('name must be a short plain name')

def parameters(seed):
    r=random.Random(seed)
    return Parameters(wind=r.randrange(3),reel_sound=r.choice((True,False)),shy=r.choice((True,False)),spare_line=r.choice((True,False)))

def initial(p):
    return {'story.ended':False,'story.outcome':'','party.location':'workshop','kite.location':'workshop','reel.owner':'Mr Vale','reel.location':'workshop','reel.borrowed':False,'reel.sound':p.reel_sound,'reel.returned':False,'kite.ready':False,'ivo.present':True,'ivo.welcomed':False,'ivo.willing':False,'ivo.ribbon_owner':'Ivo','ribbon.on_kite':False,'flight.attempted':False,'flight.airborne':False,'line.safe':False,'wind.level':p.wind,'spare.available':p.spare_line,'trust':0,'choice.returned_fault':False,'scene.optional':'','ending':''}

def validate(s):
    if s['story.ended'] != bool(s['story.outcome']): raise StoryError('Ended/outcome mismatch')
    if s['reel.returned'] and (s['reel.owner']!='Mr Vale' or s['reel.location']!='workshop'): raise StoryError('Reel return continuity')
    if s['reel.borrowed'] and s['reel.returned'] and s['reel.location']!='workshop': raise StoryError('Returned reel moved')
    if s['ribbon.on_kite'] and s['ivo.ribbon_owner']!='Ivo': raise StoryError('Ribbon ownership changed')
    if s['flight.airborne'] and (not s['line.safe'] or s['wind.level']==0): raise StoryError('Unsafe flight')
    if s['story.ended'] and (not s['reel.returned'] or s['party.location']!='workshop'): raise StoryError('Ending before return')

SCENES=('workshop','meet_neighbour','ribbon_vignette','test_flight','repair_choice','wind_vignette','final_flight','closing')
def guard(scene_id,s):
    if scene_id not in SCENES: raise StoryError(f'Unknown scene: {scene_id}')
    if s['story.ended']: return False
    return {
      'workshop':not s['kite.ready'],
      'meet_neighbour':s['kite.ready'] and not s['ivo.welcomed'],
      'ribbon_vignette':s['ivo.welcomed'] and not s['ribbon.on_kite'] and not s['flight.attempted'],
      'test_flight':s['ivo.welcomed'] and s['reel.borrowed'] and not s['flight.attempted'],
      'repair_choice':s['flight.attempted'] and not s['choice.returned_fault'],
      'wind_vignette':s['choice.returned_fault'] and s['scene.optional']=='',
      'final_flight':s['choice.returned_fault'] and not s['flight.airborne'] and not s['reel.returned'],
      'closing':s['choice.returned_fault'] and (s['flight.airborne'] or (not s['line.safe'] and s['wind.level']==0)) and not s['story.ended'],
    }[scene_id]

def prose(i,p,b,a):
    n=p.name
    texts={
    'workshop':f"At Mr Vale’s kite workshop, {n} finished an orange kite while Kit tested a wooden reel. “School club’s reel,” Mr Vale warned. “The string is frayed near the handle; bring it back.” {n} nodded, already imagining the common. Through the open door, the new neighbour watched without coming in.",
    'meet_neighbour':f"{n} asked Ivo if he wanted to join them. He held his paper bag close. “I don’t know how.” “You can watch first,” Kit said. {n} offered him the tail to hold, or space by the door. Ivo chose the tail, carefully, and stayed near enough to leave whenever he wished.",
    'ribbon_vignette':f"Ivo showed them a blue ribbon from his lunch bag. “I could lend this to the kite.” {n} checked that he meant it; he nodded. Kit tied it to the orange tail, leaving the loose end easy to untie. Ivo watched the color flicker once in the workshop light.",
    'test_flight': (f"On the common, Kit raised the kite as {n} paid out the borrowed line. A gust lifted the orange wings, then the frayed strand caught at the reel. “Stop,” {n} called. They lowered the kite safely. Ivo stepped back, looking worried; the fuzzy break was plainly at the handle." if not p.reel_sound else f"On the common, Kit raised the kite as {n} paid out the borrowed line. The reel turned cleanly and the kite climbed above the hedge. Ivo watched, then stepped closer. A rising gust tugged hard; {n} stopped the first trial before the line could strain."),
    'repair_choice':f"“I made it worse,” Ivo whispered. {n} showed him the frayed strand: it had been there before they left. Cutting it would leave Mr Vale’s reel useless. “We should tell him and stop,” {n} said. Kit wanted one more try, but agreed. They carried kite and reel back; Mr Vale listened, then offered a short spare line." if p.spare_line else f"“I made it worse,” Ivo whispered. {n} showed him the frayed strand: it had been there before they left. Cutting it would leave the borrowed reel useless. They returned it and told Mr Vale. He had no spare line. “Then we won’t fly today,” {n} said. Ivo stayed beside them as they carried the kite home.",
    'wind_vignette':f"While Mr Vale checked the reel, the gusts eased outside. Ivo watched a leaf cross the yard. “It’s slower now,” he said. {n} did not hurry him. They had lost the grand flight they expected, but the kite was intact, the fault had been reported, and the door remained open to another try.",
    'final_flight':f"Mr Vale fitted the spare line, and {n} asked Ivo again. “I’ll hold the tail,” he said. Kit raised the frame; {n} let the reel turn gently. The kite lifted in the softer wind, blue ribbon trembling. Ivo smiled, then called when he was ready to trade places. They took turns until the kite came down safely.",
    'closing':f"Back at the workshop, {n} returned the reel to Mr Vale. “It helped us find the trouble,” {n} said. Ivo untied his blue ribbon and chose to leave it on the kite. Kit asked if he would come again; Ivo nodded. The afternoon had not gone as planned, but nobody had been hurried, blamed, or left outside."
    }
    if i=='repair_choice' and not p.spare_line: return texts[i]
    return texts[i]

def play_scene(p,state,scene_id):
    if not guard(scene_id,state): raise StoryError(f'Incompatible scene: {scene_id}')
    x=LocalPlay(state,actors=('Mara','Kit','Ivo','Mr Vale'),validate=validate)
    if scene_id=='workshop':
        x.act('finish_kite',{'kite.location':'workshop'},**{'kite.ready':True})
        x.act('borrow_reel',{'reel.owner':'Mr Vale'},**{'reel.owner':'Mara','reel.borrowed':True,'reel.location':'common'})
        x.act('go_to_common',{'party.location':'workshop'},**{'party.location':'common','kite.location':'common'})
    elif scene_id=='meet_neighbour':
        x.act('offer_welcome',{'ivo.present':True},**{'ivo.welcomed':True,'trust':1})
        x.act('choose_to_join',{'ivo.welcomed':True},**{'ivo.willing':True})
    elif scene_id=='ribbon_vignette':
        x.act('lend_ribbon',{'ivo.ribbon_owner':'Ivo'},**{'ribbon.on_kite':True})
    elif scene_id=='test_flight':
        airborne=p.reel_sound and p.wind>0
        x.act('test_line',{'reel.borrowed':True},**{'flight.attempted':True,'flight.airborne':airborne,'line.safe':airborne})
    elif scene_id=='repair_choice':
        if not p.reel_sound:
            x.act('stop_and_report',{'flight.attempted':True},**{'choice.returned_fault':True,'reel.owner':'Mr Vale','reel.location':'workshop','reel.returned':True,'party.location':'workshop','kite.location':'workshop','trust':2,'line.safe':p.spare_line})
        else:
            x.act('report_wear',{'flight.attempted':True},**{'choice.returned_fault':True,'reel.owner':'Mr Vale','reel.location':'workshop','reel.returned':True,'party.location':'workshop','kite.location':'workshop','trust':2,'line.safe':p.spare_line})
    elif scene_id=='wind_vignette':
        x.act('notice_quieter_wind',{'choice.returned_fault':True},**{'scene.optional':'wind'})
    elif scene_id=='final_flight':
        if p.spare_line and p.wind>0:
            x.act('fit_spare_line',{'reel.returned':True},**{'line.safe':True})
            x.act('invite_ivo_again',{'ivo.welcomed':True},**{'ivo.willing':True,'trust':3})
            x.act('shared_launch',{'line.safe':True,'ivo.willing':True},**{'flight.airborne':True})
        else:
            raise StoryError('No safe flight is available')
    elif scene_id=='closing':
        if not x.state['reel.returned']:
            x.act('return_reel',{'reel.borrowed':True},**{'reel.owner':'Mr Vale','reel.location':'workshop','reel.returned':True,'party.location':'workshop','kite.location':'workshop'})
        outcome='shared_flight' if x.state['flight.airborne'] else 'grounded_together'
        x.act('complete_afternoon',{'reel.returned':True},**{'story.ended':True,'story.outcome':outcome,'ending':outcome})
    after=x.state
    return {'id':scene_id,'before':deepcopy(state),'after':deepcopy(after),'events':deepcopy(x.events),'text':prose(scene_id,p,state,after)}

def generate(seed=0,*,count=8,params=None):
    if type(count) is not int or count not in (7,8): raise ValueError('count must be 7 or 8')
    p=params or parameters(seed); r=random.Random(seed); attempts=0
    # Seven required encounters; the eighth is one of two optional vignettes.
    core=['workshop','meet_neighbour','test_flight','repair_choice','final_flight','closing']
    # test_flight can be followed by a return; final_flight handles safe replacement.
    optional=['ribbon_vignette','wind_vignette']
    if count==8: core.insert(2,r.choice(optional))
    state=initial(p); episodes=[]
    for sid in core:
        attempts+=1
        if not guard(sid,state):
            if sid=='final_flight' and not (p.spare_line and p.wind>0):
                # A grounded outcome is a complete final play, not a hidden flight.
                sid='closing'
                if episodes and episodes[-1]['id']=='closing': raise StoryError('Route cannot finish')
            else: raise StoryError(f'Planner produced incompatible scene {sid}')
        ep=play_scene(p,state,sid); episodes.append(ep); state=ep['after']
    if not state['story.ended']:
        # Replace the final attempted flight with an explicit grounded resolution, then close.
        x=LocalPlay(state,actors=('Mara','Kit','Ivo'),validate=validate)
        if not state['reel.returned']:
            x.act('return_reel',{'reel.borrowed':True},**{'reel.owner':'Mr Vale','reel.location':'workshop','reel.returned':True,'party.location':'workshop','kite.location':'workshop'})
        x.act('finish_grounded_play',{'reel.returned':True},**{'story.ended':True,'story.outcome':'grounded_together','ending':'grounded_together'})
        ep={'id':'closing','before':deepcopy(state),'after':deepcopy(x.state),'events':deepcopy(x.events),'text':prose('repair_choice',p,state,x.state)}
        episodes.append(ep)
    # Guarantee exact length: core has six; insert a second optional when 8 needs it.
    if len(episodes)<count:
        raise StoryError('Internal route length error')
    episodes=episodes[:count]
    if not episodes[-1]['after']['story.ended']: raise StoryError('Route did not end')
    return {'seed':seed,'parameters':asdict(p),'scene_count':count,'path':[e['id'] for e in episodes],'story':'\n\n'.join(e['text'] for e in episodes),'episodes':episodes,'final_state':episodes[-1]['after'],'search_attempts':attempts}

def replay(params,path):
    state=initial(params); out=[]
    for sid in path:
        ep=play_scene(params,state,sid); out.append(ep); state=ep['after']
    return tuple(out)

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--seed',type=int,default=0); ap.add_argument('--scenes',type=int,choices=(7,8),default=8); a=ap.parse_args(); print(generate(a.seed,count=a.scenes)['story'])
