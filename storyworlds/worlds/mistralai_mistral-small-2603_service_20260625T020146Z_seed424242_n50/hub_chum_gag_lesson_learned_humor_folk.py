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
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
REGIONS = {"home", "square", "dock"}
HUMOR_KINDS = {"kind", "wise", "playful"}
LESSON_MARKERS = {"light", "deep"}

@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = ""
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"heroine", "grandmother", "sister"}
        male = {"hero", "grandfather", "brother", "fisherman"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        mapping = {
            "hero": "Mara", "heroine": "Mara", "fisherman": "Olo",
            "grandmother": "Nana", "grandfather": "Papa"
        }
        return mapping.get(self.type, self.label or self.id)

@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)

@dataclass
class Gag:
    id: str
    phrase: str
    effect_phrase: str
    laugh_phrase: str
    kindness: str = "kind"
    tags: set[str] = field(default_factory=set)

@dataclass
class Chum:
    id: str
    label: str
    type: str
    present_phrase: str
    settles_phrase: str
    tags: set[str] = field(default_factory=set)

class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = dict(lesson_type="light", verb_learned="share")

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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

def _r_humorous_clash(world: World) -> list[str]:
    out: list[str] = []
    for hero in [e for e in world.characters() if e.type in {"hero", "heroine"}]:
        if hero.meters.get("played_gag", 0) < THRESHOLD:
            continue
        for victim in world.characters():
            if victim.id == hero.id or victim.type not in {"grandmother", "grandfather", "fisherman"}:
                continue
            surprise = victim.meters.get("surprise", 0)
            anger = victim.meters.get("anger", 0)
            if anger >= THRESHOLD and surprise >= THRESHOLD and "clash" not in world.fired:
                world.fired.add("clash")
                hero.memes["lesson_learned"] += 0.7
                out.append(f'"{hero.label_word} meant no harm," {victim.label_word} admitted softly.')
                return out
    return out

def _r_laughter_after_prank(world: World) -> list[str]:
    out: list[str] = []
    for hero in [e for e in world.characters() if e.type in {"hero", "heroine"}]:
        gag_act = hero.meters.get("played_gag", 0)
        kindness = world.facts.get("gag_kindness", "kind")
        if gag_act >= THRESHOLD and kindness == "kind" and "laughed_already" not in world.fired:
            world.fired.add("laughed_already")
            for chum in world.characters():
                if chum.type in {"fisherman", "grandfather", "grandmother"}:
                    chum.memes["amusement"] += 1
            out.append(
                f"{hero.label_word} waited, and soon {hero.pronoun('subject').capitalize()} "
                f"{'saw' if hero.type == 'heroine' else 'saw'} a smile light up {victim.label_word}'s face."
            )
            victim = next((e for e in world.characters() if e.id != hero.id), None)
            if victim:
                victim.memes["joy"] += 0.8
            return out
    return out

CAUSAL_RULES: list[Rule] = [
    Rule(name="humorous_clash", tag="social", apply=_r_humorous_clash),
    Rule(name="laughter_after_prank", tag="social", apply=_r_laughter_after_prank),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced

def introduce_village(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "clever"), "")
    world.say(
        f"In the quiet heart of the village stood {world.setting.place}, "
        f"where families gathered each evening. There lived {trait} {hero.type} "
        f"named {hero.label_word}, known for {hero.pronoun('possessive')} quick wit."
    )

def loves_gag_activity(world: World, hero: Entity, gag: Gag) -> None:
    hero.memes["trickster"] = hero.memes.get("trickster", 0) + 0.9
    world.say(
        f"{hero.label_word} loved spinning clever gags that made every day a little brighter. "
        f"Today {hero.pronoun('subject').lower()} planned to {gag.phrase}."
    )

def play_gag(world: World, hero: Entity, gag: Gag) -> bool:
    hero.meters["played_gag"] = hero.meters.get("played_gag", 0) + 1
    world.facts.update(gag_kindness=gag.kindness)

    for victim in world.characters():
        if victim.id != hero.id and victim.type in {"grandmother", "grandfather", "fisherman"}:
            surprise = victim.meters.get("surprise", 0) + 0.8
            victim.meters["surprise"] = surprise
            victim.memes["acknowledgment"] = victim.memes.get("acknowledgment", 0) + 0.1
            if surprise > THRESHOLD:
                world.say(
                    f"{victim.label_word} came out only to find " + gag.effect_phrase
                )
    return propagate(world) != []

def enter_chum(world: World, chum: Chum) -> None:
    world.say(
        f"Just then, {chum.label} {chum.present_phrase} "
        f"and rested {chum.pronoun('possessive')} walking stick against the doorframe."
    )

def chum_intervenes(world: World, hero: Entity, chum: Chum, gag: Gag) -> None:
    lesson = (
        "A gag should make hearts lighter, not heavier."
        if world.facts.get("gag_kindness") == "kind"
        else f"Even your best gags can cast a shadow if not seasoned with kindness, {hero.label_word}."
    )
    world.facts.update(lesson_delivered=lesson)
    hero.memes["lesson_learned"] = hero.memes.get("lesson_learned", 0) + 0.95
    world.say(
        f'{chum.label} chuckled and said, "Ah, {hero.label_word}... {lesson}" '
        f"{chum.settles_phrase}"
    )

def embrace_lesson(world: World, hero: Entity, lesson_marker: str) -> None:
    if lesson_marker == "deep":
        world.say(
            f"{hero.label_word} hung {hero.pronoun('possessive')} head for a moment, "
            f"then looked up with new eyes. "
            f"From that day forward, {hero.pronoun('subject')} shared even more laughter — "
            f"always with kindness at the heart."
        )
    else:
        world.say(
            f"{hero.label_word} giggled and nodded, "
            f"already dreaming up the next bright gag. "
            f"The village would remember this sunny afternoon for seasons to come."
        )

def tell(setting: Setting, gag: Gag, hero_name: str = "Mara",
         hero_type: str = "heroine", chum_type: str = "fisherman",
         marker: str = "light") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["clever", "playful"], label=hero_name,
    ))
    chum = world.add(Entity(
        id="chum", kind="character", type=chum_type,
        label={"fisherman": "Olo", "grandfather": "Papa", "grandmother": "Nana"}[chum_type],
        traits=["wise"],
    ))

    world.facts.update(hero=hero, chum=chum, gag=gag, marker=marker)

    introduce_village(world, hero)
    loves_gag_activity(world, hero, gag)

    hero.meters["rumor"] = 0.4
    world.para()

    victim = next((e for e in [chum] if e.id != hero.id), None)
    if not victim:
        victim = chum

    played = play_gag(world, hero, gag)
    if played:
        enter_chum(world, cast(Chum, victim))
        chum_intervenes(world, hero, cast(Chum, victim), gag)
        embrace_lesson(world, hero, marker)

    world.facts.update(hero_state=dict(hero.memes), victim_joy=victim.memes.get("joy", 0))
    return world

def activity_laughter(gag: Gag) -> str:
    return gag.effect_phrase or "something curious happened"

def setting_intro(setting: Setting) -> str:
    return (
        "The village hummed with afternoon warmth, lanterns swaying gently, "
        f"ready to spill golden light across the {setting.place.removeprefix('the ')}."
        if not setting.indoor
        else "The cozy room smelled of herbs and bread, a perfect place for quiet games."
    )

SETTINGS = {
    "village": Setting(place="the village hub", indoor=False, affords={"play gag"}),
    "cottage": Setting(place="the little cottage", indoor=True, affords={"play gag"}),
}

GAGS = {
    "ribbon": Gag(
        id="ribbon", phrase="tie bright ribbons to the old oak door",
        effect_phrase="Ho! What curious decorations appeared!", laugh_phrase="Ah, clever Mara!",
        kindness="kind", tags={"playful", "visual"},
    ),
    "confetti": Gag(
        id="confetti", phrase="sprinkle flowers into a visible cone",
        effect_phrase="Bewilderment filled the square with fleeting petals!",
        laugh_phrase="What a merry little storm!", kindness="kind", tags={"playful", "ephemeral"},
    ),
    "horn": Gag(
        id="horn", phrase="plant a small bladder-horn by the path",
        effect_phrase="A mournful note rose and faded into the twilight.",
        laugh_phrase="Who could resist such a jolly tune?", kindness="kind", tags={"auditory", "kind"},
    ),
}

CHUMS = {
    "fisherman": Chum(
        id="fisherman", label="Olo", type="fisherman",
        present_phrase="walked up with a net slung over one shoulder",
        settles_phrase="seated himself on the old bench and watched.",
        tags={"wise", "observant"},
    ),
    "grandfather": Chum(
        id="grandfather", label="Papa", type="grandfather",
        present_phrase="limped in leaning on a cedar cane",
        settles_phrase="settled into his favorite chair by the hearth.",
        tags={"elder", "patient"},
    ),
    "grandmother": Chum(
        id="grandmother", label="Nana", type="grandmother",
        present_phrase="carried a basket of mending and a smile",
        settles_phrase="set the basket down and began to ply her needle.",
        tags={"elder", "kind"},
    ),
}

GIRL_NAMES = ["Mara", "Lina", "Tila", "Nia", "Sofia"]
BOY_NAMES = ["Finn", "Timo", "Hoku", "Ravi", "Jens"]

def valid_combos() -> list[tuple]:
    return [(s, g.id, c.id) for s in SETTINGS
            for g in GAGS.values()
            for c in CHUMS.values()
            if s.affords.get("play gag")]

@dataclass
class StoryParams:
    place: str
    gag: str
    chum: str
    hero_name: str
    hero_gender: str
    marker: str = "light"
    seed: Optional[int] = None

KNOWLEDGE = {
    "hub": [("What is a village hub?",
             "A village hub is the heart of a small settlement where families gather, "
             "news is shared, and celebrations begin.")],
    "chum": [("What does 'chum' mean in a folk tale?",
               "In old tales, a chum is a trusted companion who brings wisdom and gentle guidance.")],
    "gag": [("What makes a folk gag different from a trick?",
             "A folk gag uses humor and cleverness to spread joy, never to harm or shame.")],
    "humor": [("Why do folk tales love humor?",
                "Humor lightens heavy loads, teaches lessons without scolding, "
                "and warms the heart like a shared fire.")],
    "lesson_learned": [("What does it mean to learn a lesson in a story?",
                       "To learn a lesson means to see a new way of acting thanks to a gentle nudge from life.")],
}

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, gag = f["hero"], f["gag"]
    return [
        f'Write a gentle folk tale in the style of a village fireside story '
        f'about {hero.label_word}, a clever hero, who spins a gag at {world.setting.place}.',
        f"Tell a short story where a playful {hero.type} named {hero.label_word} "
        f"plays a gag in {world.setting.place} and meets a wise chum who helps "
        f"{hero.pronoun('object')} see the joy of kind humor.",
        f'Make up a fireside story that includes the words "hub", "chum", and "gag" '
        f'in a light, folk-tale manner.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, gag = f["hero"], f["gag"]
    chum_word = f["chum"].label_word
    place = world.setting.place
    sub, pos = hero.pronoun("subject"), hero.pronoun("possessive")
    joy = f.get("victim_joy", 0)
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who spun the gag at {place} that made everyone laugh without hurting?"
            ),
            answer=(
                f"It was {hero.label_word}, the clever {hero.type}, "
                f"who tied bright ribbons to the oak door at the village hub."
            ),
        ),
        QAItem(
            question=(
                f"What phrase did {hero.label_word}'s chum murmur that "
                f"helped {pos} learn a lesson?"
            ),
            answer=(
                f'{chum_word} said, "A gag should make hearts lighter, '
                f'not heavier." That settled {hero.label_word}’s giggles into thoughtful delight.'
            ),
        ),
    ]
    if joy > THRESHOLD:
        qa.append(QAItem(
            question=(
                f"How could {hero.label_word} tell the gag made the chum joyful?"
            ),
            answer=(
                f'{hero.label_word} heard the chum chuckle and share '
                f'a story later about how bright the square looked with ribbon decorations.'
            ),
        ))
    if f.get("lesson_delivered"):
        qa.append(QAItem(
            question=(
                f"What lesson did {hero.label_word} learn from {chum_word} that afternoon?"
            ),
            answer=(world.facts["lesson_delivered"]),
        ))
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set()
    if f.get("gag"):
        tags.update(GAGS[f["gag"]].tags)
    for t in ["hub", "chum", "gag", "humor", "lesson_learned"]:
        if t in KNOWLEDGE:
            for q, a in KNOWLEDGE[t]:
                yield QAItem(question=q, answer=a)
    for t in ["playful", "ephemeral", "kind"]:
        if t in tags:
            for q, a in KNOWLEDGE.get(t, []):
                yield QAItem(question=q, answer=a)

def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts ==", "", "== (2) Story questions ==",
             "", "== (3) World-knowledge questions =="]
    lines = [parts[0]]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append(parts[1])
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append(parts[2])
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.characters():
        meters = {k: v for k, v in e.meters.items() if v >= THRESHOLD}
        memes = {k: v for k, v in e.memes.items() if v >= THRESHOLD}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:12} {e.type:15} {' '.join(bits)}")
    lines.append(f"  fired_rules = {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)

ASP_RULES = r"""
% A folk gag requires a played action and a chum to validate it.
gag_learned(X, Z) :- hero(X), chum(Z), played_gag(X).
lesson_valid(Y) :- gag_learned(X, Z), lesson_delivered(Y).
valid_story(P, G, C, M) :- setting(P), gag(G), chum(C), lesson_marker(M).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for gid, g in GAGS.items():
        lines.append(asp.fact("gag", gid))
        for t in sorted(g.tags):
            lines.append(asp.fact("tag", gid, t))
    for cid, c in CHUMS.items():
        lines.append(asp.fact("chum", cid))
        for t in sorted(c.tags):
            lines.append(asp.fact("tag", cid, t))
    texts = dict(
        gag_kindness=["kind", "wise"],
        lesson_marker=["light", "deep"]
    )
    for k, vs in texts.items():
        lines.append(asp.fact("param", k, *vs))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_one_example() -> tuple:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return tuple(asp.atoms(model, "valid_story")[0]) if model else ()

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale story world: hub, chum, gag, lesson learned, humor.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gag", choices=GAGS)
    ap.add_argument("--chum", choices=CHUMS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--marker", choices=["light", "deep"], default="light",
                    help="tone of the lesson learned")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true",
                    help="render the curated set of kind, wise stories")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible (place, gag, chum) triples derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.gag and args.chum:
        pass
    if args.gender and args.hero_name:
        pass

    combos = list(valid_combos())
    if not combos:
        raise StoryError("(No valid hub/chum/gag combination matches given options.)")

    place_id, gag_id, chum_id = rng.choice(sorted(combos))
    gender = args.hero_gender or rng.choice(["girl", "boy"])
    name = args.hero_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    marker = args.marker
    return StoryParams(
        place=place_id, gag=gag_id, chum=chum_id,
        hero_name=name, hero_gender=gender, marker=marker,
    )

CURATED = [
    StoryParams(place="village", gag="ribbon", chum="fisherman",
                hero_name="Mara", hero_gender="girl", marker="light"),
    StoryParams(place="cottage", gag="confetti", chum="grandmother",
                hero_name="Tila", hero_gender="girl", marker="deep"),
    StoryParams(place="village", gag="horn", chum="grandfather",
                hero_name="Hoku", hero_gender="boy", marker="light"),
]

def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], GAGS[params.gag],
                 params.hero_name, "heroine" if params.hero_gender == "girl" else "hero",
                 params.chum, params.marker)
    world_qa = list(world_knowledge_qa(world))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa,
        world=world,
    )

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        import asp
        clingo_val = set(asp.asp_valid_combos())
        python_val = set(valid_combos())
        if clingo_val == python_val:
            print(f"OK: clingo gate matches valid_combos() ({len(clingo_val)} combos).")
            return
        print("MISMATCH between clingo and valid_combos():")
        if clingo_val - python_val:
            print("  only in clingo:", sorted(clingo_val - python_val))
        if python_val - clingo_val:
            print("  only in python:", sorted(python_val - clingo_val))
        sys.exit(1)
    if args.asp:
        try:
            import asp
            model = asp.one_model(asp_program("#show valid_story/4."))
            atoms = asp.atoms(model, "valid_story")
            print(f"{len(atoms)} clingo-valid (place,gag,chum,marker) triples:\n")
            for place, gag, chum, marker in sorted(atoms):
                print(f"  {place:9} / {gag:9} / {chum:15} / {marker}")
        except Exception as e:
            print(f"ASP execution failed: {e}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (f"### {p.hero_name} and the {GAGS[p.gag].id} gag "
                      f"with {CHUMS[p.chum].label} ({p.marker} lesson)")
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
