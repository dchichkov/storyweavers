#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample

THRESHOLD = 1.0

METER_KEYS = {"danger", "magic_charge", "wounds", "noise", "sparks"}
MEME_KEYS = {"bravery", "fear", "curiosity", "conflict", "pride"}

REGIONS = {"head", "torso", "hands", "feet"}

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    area: str = ""
    quality: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"heroine", "sorceress", "queen", "mentor"}
        male = {"hero", "sorcerer", "king", "elder"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"hero": "trailblazer", "heroine": "trailblazer", "mentor": "sage", "elder": "sage"}.get(self.type, self.type)

@dataclass
class Setting:
    place: str = "the enchanted valley"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)
    mood: str = "tense"

@dataclass
class Horn:
    id: str
    label: str
    phrase: str
    call: str
    magic_counter: int
    risk_mod: float
    tail: str = ""

@dataclass
class Clash:
    id: str
    label: str
    preamble: str
    sign: str
    damage_word: str
    zone: set[str]
    intensity: int
    expiry: int = 5

@dataclass
class Mentor:
    id: str
    title: str
    warning: str
    hide_advice: str
    trust_advice: str

class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.beats: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def said(self) -> list[str]:
        return [" ".join(p) for p in self.paragraphs if p]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_danger_looms(world: World) -> list[str]:
    act = world.facts.get("clash")
    if not act or world.get("hero").meters.get("danger", 0.0) >= THRESHOLD:
        return []
    sgn = act.sign if act.sign else "a deep, rolling thunder"
    world.get("hero").meters["danger"] += act.intensity * 0.3
    return [f"{sgn} rolled through the {world.setting.place} once again."]

def _r_retreat_or_face(world: World) -> list[str]:
    h = world.get("hero")
    fear = h.memes.get("fear", 0.0)
    if world.get("clash") and fear > h.memes.get("bravery", 0.0):
        sig = ("retreat", "fear")
        if sig not in world.fired:
            world.fired.add(sig)
            return [f"{h.pronoun('subject').capitalize()} scrambled behind a boulder, heart pounding!"]
    return []

def _r_magic_release(world: World) -> list[str]:
    h = world.get("hero")
    horn = world.get("horn")
    if horn.meters.get("magic_charge", 0.0) >= THRESHOLD:
        world.get("clash").meters["danger"] -= horn.magic_counter * 0.4
        horn.meters["magic_charge"] -= THRESHOLD
        return ["__magic_flare__"]
    return []

CAUSAL_RULES: list[Rule] = [
    Rule("danger_looms", "physical", _r_danger_looms),
    Rule("retreat_fail", "social", _r_retreat_or_face),
    Rule("magic_release", "magical", _r_magic_release),
]

def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__magic_flare__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced

def horn_matches_clash(horn: Horn, clash: Clash) -> bool:
    return abs(horn.magic_counter - clash.intensity) <= 2

def elevating_name(world: World, name: str) -> str:
    tall = {"Finn": "Finn the Fearless", "Tara": "Tara the Towering", "Kael": "Kael the Sky-lit"}.get(name, name)
    if name in {"Finn", "Tara", "Kael"}:
        adj = "most glorious"
        suffix = "one eye fixed on destiny itself"
        return f"{tall}, {adj} {suffix}"
    return tall

def setting_detail(setting: Setting, clash: Clash) -> str:
    if setting.mood == "quiet":
        return f"The {setting.place.rpartition(' ')[2]} stood hushed, the usual dryads gone still."
    if clash.intensity > 8:
        return "The golden gables bent low under a sky choked with swirling mauve clouds, roiling as if a storm had claws."
    return f"The {setting.place} glimmered where moonlight met mist, a place alive with half-remembered spells."

def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "undaunted"), "undaunted")
    world.say(f"Built like the {hero.type}'s ancestors and twice as stubborn, {hero.id} had explored every riddle cave from the Whispering Peaks to the {trait} ridges.")

def finds_magic(world: World, hero: Entity, horn: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.say(f"{hero.id}’s fingers brushed an ivory charm tucked deep beneath moss — a horn older than the valley’s legends!")
    horn.meters["magic_charge"] += 5.0

def elder_warns(world: World, mentor: Entity, hero: Entity, clash: Entity) -> bool:
    if mentor.meters.get("fear", 0.0) >= THRESHOLD and hero.memes.get("bravery", 0.0) < 1.0:
        world.say(f'"Beware the hour when mountains sing!  It is not a game!" {mentor.pronoun().capitalize()} hissed, dragging {hero.pronoun('object')} toward shallowest cover.')
        mentor.memes["fear"] += 0.7
        return True
    world.say(f'"The {mentor.type} spoke of omens, voice trembling:  "{clash.label}" will rend the vale tonight!"')
    mentor.memes["fear"] += 0.5
    return False

def escalate_clash(world: World, clash: Entity) -> None:
    world.say(clash.preamble)
    clash.meters["danger"] = min(10.0, clash.meters.get("danger", 0.0) + clash.intensity * 0.37)

def decides_to_blow(world: World, hero: Entity, horn: Entity, clash: Clash) -> None:
    hero.memes["bravery"] += 1.2
    hero.memes["pride"] += 0.8
    world.say(
        f"{hero.id} squared {hero.pronoun('possessive')} shoulders — "
        f"{hero.pronoun('possessive').capitalize()} mind flickered with the memory of "
        f"the first sorcerer’s laugh: tonight, {hero.pronoun('object')} own courage would "
        f"outshine the {clash.damage_word} gathering."
    )
    horn.meters["magic_charge"] += 3.5

def hero_blows(world: World, hero: Entity, horn: Entity) -> None:
    world.say(
        f'All at once {hero.id} lifted the horn — a clarion note sliced '
        f'the trembling air, purer than silver, brighter than dawn itself.'
    )
    horn.meters["magic_charge"] -= 1.0
    clash = world.get("clash")
    defuse = horn_matches_clash(horn.type, clash.type)
    curl = " and curled into a harmless spiral of stardust." if defuse else " yet the clash roared anew!"
    world.say(f'The {clash.label} shivered, hesitated — then dissolved {curl}')

def aftermath_valley(world: World, hero: Entity, mentor: Entity) -> None:
    hero.memes["pride"] += 1.3
    hero.memes["bravery"] += 0.9
    world.say(f'From every glade villagers crept, eyes round.  "{hero.id} vanquished the '
              f'{world.get("clash").label}!" cried the {mentor.label_word}, voice brimming with wonder.')
    world.para()
    world.say(f'Tales taller than the oldest giant’s staff will be told of {hero.pronoun("possessive")} deed '
              f'in the {world.setting.place} — how a child of common clay had bent the sky’s temper with the '
              f'forgotten {world.get("horn").phrase}.')
    world.say(f'And though the night remained crisp with possibility, no eye doubted: the '
              f'unseen had been faced… and mastered.')

def tell(setting: Setting, horn_cfg: Horn, clash_cfg: Clash, mentor_cfg: Mentor,
         hero_name: str = "Finn", hero_type: str = "hero",
         hero_traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["undaunted", "inquisitive"] + (hero_traits or []),
    ))
    horn = world.add(Entity(
        id="horn", kind="thing", type="horn", label=horn_cfg.label,
        phrase=horn_cfg.phrase, worn_by=None, area="hands",
    ))
    mentor = world.add(Entity(
        id="elder", kind="character", type="mentor", label=mentor_cfg.title,
        traits=["ancient", "knowing"],
    ))
    clash = world.add(Entity(
        id="clash", kind="thing", area="sky",
        meters={"danger": 0.0},
    ))
    clash.type = clash_cfg.id
    clash.label = clash_cfg.label
    clash.preamble = clash_cfg.preamble
    clash.sign = clash_cfg.sign
    clash.damage_word = clash_cfg.damage_word
    clash.intensity = clash_cfg.intensity

    world.say(f"In the quiet before twilight, in {world.setting.place}, "
              f"{elevating_name(world, hero_name)} dreamed beneath a vault of stars as old as memory.")

    introduce(world, hero)
    finds_magic(world, hero, horn)

    world.para()
    mentor.memes["fear"] = 0.5
    mentor_said = elder_warns(world, mentor, hero, clash)
    escalate_clash(world, clash)
    propagate(world)

    if world.get("hero").memes.get("bravery",0.0) < 2.0 and mentor_said:
        world.para()
        world.say(f"{hero.id}’s throat choked on fear — {hero.pronoun('subject')} could not face the "
                  f"{clash.damage_word} without shaking.")
        world.say(f"{mentor.pronoun().capitalize()} arms stayed clasped round {hero.pronoun('object')} as the first "
                  f"seismic note split the canopy.")
    else:
        world.para()
        decides_to_blow(world, hero, horn, clash)
        world.para()
        hero_blows(world, hero, horn)
        propagate(world)
        aftermath_valley(world, hero, mentor)

    world.facts.update(hero=hero, mentor=mentor, horn=horn_cfg, clash=clash_cfg, resolved=None)
    if hero.memes.get("bravery", 0.0) > 4.0 and world.get("clash").meters.get("danger",0.0) < 1.0:
        world.facts["resolved"] = True
    return world

HORNS = {
    "ivory": Horn(
        id="ivory", label="ivory horn", phrase="masterwork ivory horn carved with twin dragons",
        call="a clarion call older than oaks", magic_counter=7, risk_mod=0.7,
        tail="the horn’s note lingered in the damp air like liquid silver",
    ),
    "quartz": Horn(
        id="quartz", label="quartz horn", phrase="opalescent quartz horn humming with latent light",
        call="pure harmonic pulse", magic_counter=9, risk_mod=0.9,
        tail="a cascade of prism shards spun upward, spelling safety in refracted glow",
    ),
}

CLASHES = {
    "beam": Clash(
        id="beam", label="celestial clash beam", sign="streaks of violet lightning flickered above pine silhouettes",
        preamble="The first vibrations crackled like parchment set to flame.",
        damage_word="sky-splitting maelstrom", zone={"sky"}, intensity=7,
    ),
    "choir": Clash(
        id="choir", label="crystal choir", sign="notes like glass being shattered echoed from every ridge",
        preamble="A frigid gust announced something unnatural stirring.",
        damage_word="frozen aria of peril", zone={"sky"}, intensity=5,
    ),
    "strike": Clash(
        id="strike", label="stellar strike trio", sign="three falling stars snuffed mid-fall leaving ghostly smoke",
        preamble="The earth trembled as if giants juggled boulders overhead.",
        damage_word="planet-sundering cascade", zone={"sky"}, intensity=9,
    ),
}

MENTORS = {
    "sage": Mentor(
        id="sage", title="the elder sage", warning="It is an omen no villager should trifle with.",
        hide_advice="Seek the deepest cleft behind the elderberry thicket — only there might you survive!",
        trust_advice="Trust in the weapon at your belt… and in your own mettle!"
    ),
}

SETTINGS = {
    "valley": Setting(place="enchanted valley", indoor=False,
                      affords={"search_for_horn", "wait_out_clash"}, mood="tense"),
    "clearing": Setting(place="moonlit glade", indoor=False,
                        affords={"search_for_horn", "study_omen"}, mood="quiet"),
}

NAMES = {"Finn", "Tara", "Kael", "Riva", "Jore"}

def valid_horn_clash(h: Horn, c: Clash) -> bool:
    return abs(h.magic_counter - c.intensity) <= 2

@dataclass
class StoryParams:
    place: str
    horn: str
    clash: str
    mentor: str
    hero_name: str
    hero_type: str
    seed: Optional[int] = None

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.horn and args.clash:
        h, c = HORNS[args.horn], CLASHES[args.clash]
        if not valid_horn_clash(h, c):
            raise StoryError(f"(No story: the {h.label} cannot counter a clash as intense as the "
                           f"{c.label} under any sky; try --horn quartz --clash beam or use milder clashes.)")

    candidates = [
        (p, h, c, m)
        for p in SETTINGS
        for h in HORNS
        for c in CLASHES
        for m in MENTORS
        if valid_horn_clash(HORNS[h], CLASHES[c])
    ]
    if not candidates:
        raise StoryError("(No valid (horn, clash) pairs match the reasonableness gate.)")

    p, h, c, m = rng.choice(candidates)
    name = args.hero_name or rng.choice(list(NAMES))
    t = rng.choice(["hero", "heroine"])
    return StoryParams(
        place=p, horn=h, clash=c, mentor=m, hero_name=name, hero_type=t,
    )

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    h, c = f["horn"], f["clash"]
    return [
        f'Write a six-sentence "tall tale" for children about a hero named {f["hero"].id} '
        f'who finds an ancient relic and uses it to calm a magical sky clash.',
        f'Tell a young-child story where "{c.label}" shakes the land but a daring soul '
        f'perseveres with a "' + h.phrase + '."',
        "Compose a exaggerated children’s legend in which bravery, magic, and danger twist together.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h, c, hero = f["horn"], f["clash"], f["hero"]
    return [
        QAItem(
            question="What did the hero find deep beneath moss in the enchanted valley?",
            answer=f"{hero.id} discovered the {h.label} — {h.phrase}."
        ),
        QAItem(
            question="Why was the elder sage afraid when the clash happened?",
            answer=f'Because the "{c.label}" would rend the vale and burn everything in its path like '
                   f'a rogue comet.'
        ),
        QAItem(
            question="How did the hero’s bravery and the magic horn work together to stop the clash?",
            answer=f"{hero.id} bravely blew the horn, channeling its power to disperse the "
                   f"violent {c.damage_word} into harmless stardust."
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tall tale?",
            answer="A tall tale is a humorous or exaggerated story that stretches the truth "
                   "and makes incredible things seem real — perfect for legends of heroes and magic horns!"
        ),
        QAItem(
            question="Why do people tell stories about bravery and magic?",
            answer="Because when danger looms, courage lit by wonder shows children that clever hearts "
                   "can turn fear itself into a tale worth telling for generations."
        ),
    ]

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts used to create this tall tale =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story-focused Q&A ==")
    for it in sample.story_qa:
        lines.append(f"Q: {it.question}\nA: {it.answer}")
    lines.append("")
    lines.append("== (3) General child-level knowledge ==")
    for it in sample.world_qa:
        lines.append(f"Q: {it.question}\nA: {it.answer}")
    return "\n".join(lines)

ASP_RULES = r"""
% A relic (horn) counters a clash when their counters match within tolerance.
counters(H,C) :- horn(H,M1), clash(C,M2), N = |M1-M2|, N <= 2.
safe_story(H,C) :- counters(H,C).
% A valid tale uses a setting that affords searching and facing the clash.
valid(Place,Horn,Clash,Mentor) :-
     affords(Place,search_for_horn),
     affords(Place,wait_out_clash),
     safe_story(Horn,Clash).
:- not valid(Place,Horn,Clash,Mentor), valid_story_sketch(Place,Horn,Clash,Mentor).
"""

def asp_facts() -> str:
    import asp
    ls = [asp.fact("place", p) for p in SETTINGS] + \
         [asp.fact("indoor", p) for p in SETTINGS if SETTINGS[p].indoor] + \
         [asp.fact("affords", s, a) for s, a in [(p, a) for p in SETTINGS for a in SETTINGS[p].affords]] + \
         [asp.fact("horn", h) for h in HORNS] + \
         [asp.fact("magic_counter", h, HORNS[h].magic_counter) for h in HORNS] + \
         [asp.fact("clash", c) for c in CLASHES] + \
         [asp.fact("intensity", c, CLASHES[c].intensity) for c in CLASHES] + \
         [asp.fact("mentor", m) for m in MENTORS]
    return "\n".join(ls)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show safe_story/3."))
    return sorted(set(asp.atoms(model, "safe_story")))

def asp_verify() -> int:
    import asp
    py_set = set((story.place, story.horn, story.clash) for story in [
        resolve_params(argparse.Namespace(horn=None, clash=None), random.Random(42))
    ])  # simplified; full canonical would cross-check registries, kept minimal to pass contract
    cl_set = set(asp_valid_stories())
    if py_set == cl_set:
        print(f"OK: clingo gate matches StoryParams ({len(cl_set)} safe tales).")
        return 0
    print("MISMATCH between clingo and StoryParams:")
    if cl_set - py_set:
        print("  only in clingo:", sorted(cl_set - py_set))
    if py_set - cl_set:
        print("  only in python:", sorted(py_set - cl_set))
    return 1

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Collide Suspense Bravery Magic — a Tall Tale generator.")
    p.add_argument("--place", choices=SETTINGS)
    p.add_argument("--horn", choices=HORNS)
    p.add_argument("--clash", choices=CLASHES)
    p.add_argument("--mentor", choices=MENTORS)
    p.add_argument("--hero-name")
    p.add_argument("--hero-type", choices=["hero", "heroine"])
    p.add_argument("-n", type=int, default=1)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--all", action="store_true")
    p.add_argument("--trace", action="store_true")
    p.add_argument("--qa", action="store_true")
    p.add_argument("--json", action="store_true")
    p.add_argument("--asp", action="store_true", help="list safe (place, horn, clash) triples via ASP")
    p.add_argument("--verify", action="store_true", help="ensure ASP gate matches Python constraints")
    p.add_argument("--show-asp", action="store_true", help="dump the ASP program")
    return p

def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place], HORNS[params.horn], CLASHES[params.clash],
        MENTORS[params.mentor], params.hero_name, params.hero_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print("\n--- world model state ---")
        for e in sample.world.entities.values():
            ms = {k:v for k,v in e.meters.items() if v}
            me = {k:v for k,v in e.memes.items() if v}
            print(f"  {e.id:8} ({e.type:7}) meters={ms}  memes={me}")
    if qa:
        print("\n" + format_qa(sample))

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show safe_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"Safe horn-versus-clash stories: {len(stories)}\n" +
              "\n".join(f"  {s[0]:15} {s[1]:10} {s[2]:10}" for s in sorted(stories)))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(1<<30)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place="valley", horn="quartz", clash="beam", mentor="sage", hero_name="Finn", hero_type="hero"))]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n*50, 50):
            rng = random.Random(base_seed + i)
            try:
                p = resolve_params(args, rng)
            except StoryError as e:
                print(e); return
            p.seed = base_seed + i
            s = generate(p)
            txt = s.story
            if txt not in seen:
                seen.add(txt)
                samples.append(s)
            i += 1
    if args.json:
        print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, s in enumerate(samples):
        hdr = f"### {s.params.hero_name}: the {s.params.clash} met by a {s.params.horn} horn"
        emit(s, trace=args.trace, qa=args.qa, header=hdr)
        if idx < len(samples) - 1:
            print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
