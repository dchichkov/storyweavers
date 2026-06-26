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

# Add storyworlds/ to sys.path for direct execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0  # State magnitude needed for narration

@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # "sleuth", "friend", "clue", "ribbon" ...
    label: str = ""                # short reference, e.g. "the scarf"
    phrase: str = ""               # full noun phrase, e.g. "a crumpled theater ticket"
    traits: list[str] = field(default_factory=list)
    relationship: Optional[str] = None  # friendship links between characters
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    region: str = ""                  # spatial region for pattern matching
    plural: bool = False              # pronoun handling
    # Simulation state dimensions
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical state
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional state

    def pronoun(self, case: str = "subject") -> str:
        subject_map = {"sleuth": "they", "friend": "they", "sheriff": "she", "witness": "he"}
        object_map = {"sleuth": "them", "friend": "them", "sheriff": "her", "witness": "him"}
        possessive_map = {"sleuth": "their", "friend": "their", "sheriff": "her", "witness": "his"}
        kind_map = {"sleuth": "detective", "friend": "pal", "sheriff": "officer", "witness": "informant"}
        type_map = {"sleuth": "sleuths", "friend": "friends", "sheriff": "sheriff", "witness": "folks"}

        if self.type in subject_map:
            return {
                "subject": subject_map[self.type],
                "object": object_map[self.type],
                "possessive": possessive_map[self.type],
                "kind": kind_map[self.type],
                "type": type_map[self.type]
            }[case]
        return {
            "subject": "it" if not self.plural else "they",
            "object": "it" if not self.plural else "them",
            "possessive": "its" if not self.plural else "their",
        }[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

# Domain configuration types
@dataclass
class Setting:
    place: str = "Shell Harbor's Mystery Lane"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)  # which investigations this place hosts

@dataclass
class Clue:
    id: str
    label: str = "clue"
    description: str = "a scrap of evidence"
    sensory_details: dict[str, str] = field(default_factory=dict)  # typical observations
    difficulty: float = 1.0  # how much attention needed to notice

@dataclass
class Suspect:
    name: str
    traits: list[str]
    motive: str = "unknown"
    presence: float = 1.0  # confidence in alibi
    relationship_to_victim: Optional[str] = None

@dataclass
class Mystery:
    id: str
    title: str
    suspects: list[str]
    required_clues: set[str]
    resolution_phrase: str = ""  # thematic line for the solution
    tags: set[str] = field(default_factory=set)  # topics like "swoon", "theater"

class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.noted_regions: set[str] = set()
        self.current_relationships: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.noted_regions = set(self.noted_regions)
        clone.paragraphs = [[]]
        clone.current_relationships = copy.deepcopy(self.current_relationships)
        return clone

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

# Causal rule system
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _notice_clue(world: World) -> list[str]:
    out: list[str] = []
    for char in world.characters():
        if char.memes["observation"] < THRESHOLD: continue
        for clue in [e for e in world.entities.values() if e.type == "clue"]:
            if clue.id in [x.id for x in world.fired]: continue
            region = clue.region or "center"
            world.fired.add((clue.id,))
            details = random.choice(list(clue.sensory_details.values())) if clue.sensory_details else "odd"
            out.append(
                f"{char.pronoun().capitalize()} noticed {details} near "
                f"{region} that might help solve the {world.facts.get('mystery_title', 'mystery')}."
            )
    return out

def _swoon_response(world: World) -> list[str]:
    out: list[str] = []
    for char in world.characters():
        if char.memes.get("swoon", 0.0) >= THRESHOLD:
            pair = world.current_relationships.get(char.id, {}).get("closest_friend", char.id)
            if pair == char.id: continue  # self
            friend = world.get(pair)
            sig = ("swoon", char.id, friend.id)
            if sig in world.fired: continue
            world.fired.add(sig)
            reaction = random.choice([
                f"{char.pronoun().capitalize()} felt a flutter that made {char.pronoun('object')} look twice.",
                f"Something about this made {char.pronoun('subject')} get all tingly inside.",
                f"{char.pronoun().capitalize()} had a sudden urge to share this with {friend.pronoun('object')}."
            ])
            out.append(reaction)
    return out

def _friendship_fortify(world: World) -> list[str]:
    out: list[str] = []
    for a, b_dict in world.current_relationships.items():
        friend_level = b_dict.get("closest_friend", 0.0)
        if friend_level >= THRESHOLD:
            if ("fortify", a, list(b_dict.keys())[0]) in world.fired: continue
            friend = world.get(list(b_dict.keys())[0])
            world.fired.add(("fortify", a, friend.id))
            out.append(
                f"The bond between {a} and {friend.id} deepened—friendship meant "
                f"they would face this together."
            )
    return out

CAUSAL_RULES: list[Rule] = [
    Rule(name="notice", tag="detection", apply=_notice_clue),
    Rule(name="swoon", tag="emotion", apply=_swoon_response),
    Rule(name="fortify", tag="social", apply=_friendship_fortify),
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
                produced.extend(s for s in sents if s != "__evt__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced

# Reasonableness constraints
def valid_mystery_clues(mystery: Mystery, clues: list[Clue]) -> bool:
    clue_ids = {c.id for c in clues}
    return mystery.required_clues.issubset(clue_ids)

def mystery_supports_friendship(mystery: Mystery) -> bool:
    return "friendship" in mystery.tags or "swoon" in mystery.tags

@dataclass
class StoryParams:
    setting: str
    mystery: str
    sleuth_a: str
    sleuth_b: str
    clue_pool: list[str]
    seed: Optional[int] = None

SETTINGS = {
    "mystery_lane": Setting(
        place="Shell Harbor's Mystery Lane",
        indoor=False,
        affords={"investigate", "notice", "chase"},
    ),
    "theater": Setting(
        place="Grand Shell Theater stage left",
        indoor=True,
        affords={"notice", "spectate"},
    ),
    "harbor_walk": Setting(
        place="sunset Harbor boardwalk",
        indoor=False,
        affords={"investigate", "chase", "notice"},
    ),
}

CLUES = {
    "theater_ticket": Clue(
        id="theater_ticket",
        label="ticket stub",
        description="a crumpled yellow theater ticket",
        sensory_details={"sight": "yellow ticket stub printed with ornate script",
                       "touch": "slightly crinkled paper edges",
                       "scent": "whispers of popcorn and cologne"},
        difficulty=0.7,
    ),
    "love_note": Clue(
        id="love_note",
        label="note",
        description="tiny folded paper with a message",
        sensory_details={"sight": "pale blue paper folded into a star shape",
                       "touch": "paper smooth as polished shell"},
        difficulty=0.9,
    ),
    "scarf": Clue(
        id="scarf",
        label="plaid scarf",
        description="knitted wool scarf draped on railing",
        sensory_details={"sight": "red-and-green plaid wool scarf hanging loose",
                       "touch": "soft knit ridges under fingertips"},
        difficulty=0.8,
    ),
    "ribbon": Clue(
        id="ribbon",
        label="ribbon",
        description="blue silk ribbon tied to lamppost",
        sensory_details={"sight": "frayed blue silk fluttering around iron post",
                       "touch": "smooth silk surface shifting in breeze"},
        difficulty=0.5,
    ),
    "ticket_residue": Clue(
        id="ticket_residue",
        label="residue",
        description="dusty mark on program counter",
        sensory_details={"sight": "fine tan powder glinting under mantle light",
                       "scent": "faint residue of candy and ink"},
        difficulty=0.6,
    ),
}

MYSTERIES = {
    "missing_note": Mystery(
        id="missing_note",
        title="the missing theater note",
        suspects=["sheriff_raine", "stagehand_marnie", "usher_jules"],
        required_clues={"love_note", "theater_ticket", "ticket_residue"},
        resolution_phrase="Solving it together made their friendship even stronger.",
        tags={"swoon", "friendship", "theater", "cluehunt"},
    ),
    "scarf_heist": Mystery(
        id="scarf_heist",
        title="the scarf snatcher",
        suspects=["park_ranger_lee", "ice_cream_al", "mail_carol"],
        required_clues={"scarf", "ribbon", "ticket_residue"},
        resolution_phrase="The lost-and-found box proved treasure belongs where kindness lives.",
        tags={"friendship", "swoon", "mystery"},
    ),
}

NAMES = {
    "sleuths": ["Alex", "Sam", "Jamie", "Taylor"],
    "friends_male": ["Leo", "Ben", "Casey", "Riley"],
    "friends_female": ["Mira", "Zoe", "Ava", "Noor"],
}

def build_settings_compat() -> dict[str, dict]:
    compat = defaultdict(dict)
    for sid, s in SETTINGS.items():
        for mid in MYSTERIES:
            m = MYSTERIES[mid]
            clues = {cid: CLUES[cid] for cid in m.required_clues}
            if valid_mystery_clues(m, list(clues.values())):
                compat[sid][mid] = list(clues.keys())
    return compat

COMPATIBLE = build_settings_compat()

# Narrative verbs
def establish_detectives(world: World, a_name: str, b_name: str) -> None:
    a_pronouns = world.add(Entity(
        id=a_name, kind="character", type="sleuth",
        label="Alex", traits=["observant", "slightly dramatic"],
    ))
    b_pronouns = world.add(Entity(
        id=b_name, kind="character", type="friend",
        label="Sam", traits=["logical", "patient"],
    ))
    a_pronouns.relationship = "closest_friend"
    b_pronouns.relationship = "closest_friend"
    world.current_relationships[a_name][b_name] = 1.2
    world.current_relationships[b_name][a_name] = 1.2
    world.say(
        f"{a_name.capitalize()} and {b_name} were the town’s best "
        f"{a_pronouns.type}s, famous for solving every {world.setting.place} mystery together."
    )

def wander_to_scene(world: World, setting_obj: Setting, mystery_obj: Mystery) -> None:
    mood = "soft golden light" if not setting_obj.indoor else "hushed theater glow"
    world.say(
        f"One evening, as {mood} painted the {world.setting.place}, "
        f"{mystery_obj.title} awaited them."
    )
    world.say(
        f"The crisp air carried the scent of salt and something oddly sweet—"
        f"like {random.choice(['a memory half-remembered', 'a promise yet unspoken'])}."
    )

def discover_clues(world: World, clue_ids: list[str]) -> None:
    world.para()
    world.say("First they split up, scanning for anything out of place.")
    for cid in clue_ids:
        clue = CLUES[cid]
        finder = random.choice(world.characters())
        finder.memes["observation"] += 0.3
        world.entities[clue.id].region = random.choice(["near proscenium", "by lamppost 7", "stuck in grate"])
        world.say(
            f"{finder.pronoun().capitalize()} spotted {clue.description} "
            f"{random.choice(['half-hidden under bench', 'caught in lamplight', 'tucked between bricks'])}."
        )

def note_the_unusual(world: World, mystery: Mystery) -> None:
    diff = sum(c.difficulty for c in CLUES.values())
    notice = "together" if diff > 2.8 else "in turn"
    world.say(
        f"Together they pieced together what had happened: {mystery.resolution_phrase or 'some things are meant to be found only when trusted friends look.'}"
    )
    for char in world.characters():
        char.memes["swoon"] += 0.4
    propagate(world)

def share_the_findings(world: World, a_name: str, b_name: str) -> None:
    world.para()
    resp = random.choice([
        f"Both felt a flutter—a warm thrill of ‘we did it together',",
        f"A swoon of pride ran through them like theater spotlights coming up.",
        f"Something glimmered between them—proof that friendship carried them farther than fear."
    ])
    world.say(resp)
    world.say(
        f"{a_name.capitalize()} grinned and said, \"Best partnership Shell Harbor’s ever known.\" "
        f"\"Agreed,\" {b_name} replied, smiling back.\n\n"
        "And with the last clue tucked safely, their bond felt brighter than ever."
    )

def tell_story(setting_name: str, mystery_id: str, clue_ids: list[str],
               sleuth_a: str = "Alex", sleuth_b: str = "Sam") -> World:
    world = World(SETTINGS[setting_name])
    mystery_obj = MYSTERIES[mystery_id]

    # Act 1: Meet the sleuths & set context
    establish_detectives(world, sleuth_a, sleuth_b)
    world.facts.update(setting=setting_name, mystery_title=mystery_obj.title)

    # Act 2: Arrive at mystery setting
    wander_to_scene(world, world.setting, mystery_obj)

    # Act 3: Investigate & collect clues
    discover_clues(world, clue_ids)

    # Act 4: Synthesize observations and feel emotional beat
    note_the_unusual(world, mystery_obj)

    # Act 5: Celebrate with emotional resolution
    share_the_findings(world, sleuth_a, sleuth_b)

    world.facts.update(
        mystery_id=mystery_id, sleuths=(sleuth_a, sleuth_b),
        clues_found=clue_ids, resolution_sentence=mystery_obj.resolution_phrase
    )
    return world

# Q&A generation
def generation_prompts(world: World) -> list[str]:
    heroes = ", ".join(world.facts["sleuths"])
    tags = world.facts.get("mystery_id") or "mystery"
    return [
        f"Write a gentle 3–5 year-old detective tale titled '{world.facts['mystery_title']}' "
        f"using the word 'swoon' in the second paragraph.",
        f"Craft a tiny story where best friends {heroes} investigate a {tags} in Shell Harbor. "
        f"Include a moment where they feel a strong happy ‘swoon' together.",
        f"Tell a cozy mystery where little friends solve a puzzle and friendship grows warmer "
        f"while noticing shiny clues like theater tickets and silk ribbons.",
    ]

def story_qa(world: World) -> list[QAItem]:
    heroes = world.facts["sleuths"]
    a, b = heroes[0], heroes[1]
    qa: list[QAItem] = [
        QAItem(
            question=f"Who are the two best friends solving the mystery?",
            answer=f"They are {a} and {b}, partners in Shell Harbor’s tiny detective circle."
        ),
        QAItem(
            question=f"What first caught their attention that led to the scarf clue?",
            answer="The breeze carried the faintest whisper of popcorn and old ink, "
                   "so they looked twice near the proscenium."
        ),
    ]
    src = world.facts.get("mystery_title", "mystery")
    qa.append(QAItem(
        question=f"How did solving this {src} make their friendship feel?",
        answer=(
            f"When the last ribbon fluttered into place, both felt a warm swoon "
            f"that glowed between them—proof their bond was as bright as any stage light."
        )
    ))
    return qa

KNOWLEDGE = {
    "sleuth": [("What is a sleuth?", "A sleuth is a friend who helps solve little puzzles— "
               "like who took the last cookie or why the lamppost ribbon floated alone.")],
    "swoon": [("What does swoon mean?", "To swoon means your heart feels so full of happy it "
               "makes your chest warm and your cheeks pink, like a kitten curled up in your lap.")],
    "clue": [("What is a clue in a mystery?", "A clue is anything that twinkles differently "
             "than the rest—like a ticket that glints under the stage light or a scarf "
             "waving from a lamppost.")],
    "friendship": [("Why is friendship important?", "Friends share quiet things—the first star, "
                   "the last cookie, the way a mystery makes your heart flutter together.")],
    "theater": [("What happens at a theater?", "A theater is a special room with pretty lights "
                "where grown-ups play pretend stories on a stage and kids watch with wide eyes.")],
}

def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"sleuth", "clue", "theater"} | set(world.facts.get("mystery_id", "").split("_"))
    if "swoon" in world.facts.get("mystery_id", ""):
        tags.add("swoon")
    if "friendship" in world.facts.get("mystery_id", ""):
        tags.add("friendship")

    out: list[QAItem] = []
    for tag in ["sleuth", "swoon", "clue", "friendship", "theater"]:
        if tag in tags:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[tag])
    return out

# ASP twin
ASP_RULES = r"""
% A valid story has two detectives who investigate compatible clues for a mystery in a compatible place.
valid_set(Place, Mystery, SleuthA, SleuthB) :-
    setting(Place), mystery(Mystery), detective(SleuthA), detective(SleuthB),
    includes_clues(Mystery, C), clue_pool(C),
    sleuth_pair(SleuthA, SleuthB).

includes_clues(M, C) :- mystery_clues(M, X), subset(X, C).
sleuth_pair(A, B) :- friend_pair(A, B).

% Mystery-swoon-friendship trio only
valid_swoon_story(P, M, A, B) :- valid_set(P, M, A, B), mystery_has_tag(M, swoon), mystery_has_tag(M, friendship).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    # Settings
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))

    # Clues
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        for k, v in c.sensory_details.items():
            lines.append(asp.fact("sensory", cid, k, v))
        lines.append(asp.fact("difficulty", cid, round(c.difficulty,1)))

    # Mysteries
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("mystery_title", mid, m.title))
        for sid in m.required_clues:
            lines.append(asp.fact("mystery_clues", mid, sid))
        for t in m.tags:
            lines.append(asp.fact("mystery_has_tag", mid, t))

    # Detectives
    lines.append(asp.fact("detective", "Alex"))
    lines.append(asp.fact("detective", "Sam"))
    lines.append(asp.fact("friend_pair", "Alex", "Sam"))
    lines.append(asp.fact("clue_pool", "theater_ticket", "love_note", "scarf", "ribbon", "ticket_residue"))

    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import asp
    py_set = {(p, m, "Alex", "Sam") for p, m in COMPATIBLE.items()}
    clingo_set = set(asp.atoms(asp.one_model(asp_program("#show valid_swoon_story/4.")), "valid_swoon_story"))
    if py_set == clingo_set:
        print(f"OK: clingo gate matches detector ({len(clingo_set)} stories).")
        return 0
    print("Mismatch between clingo and Python gate.")
    if py_set - clingo_set:
        print("Missing in clingo:", sorted(py_set - clingo_set))
    if clingo_set - py_set:
        print("Extra in clingo:", sorted(clingo_set - py_set))
    return 1

# CLI interface
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny detective-tale storyworld: two sleuths, "
                                      "a swoon-worthy mystery, and a friendship worth solving for.")
    ap.add_argument("--setting", choices=SETTINGS, default="mystery_lane")
    ap.add_argument("--mystery", choices=MYSTERIES, default="missing_note")
    ap.add_argument("--sleuth_a", default="Alex")
    ap.add_argument("--sleuth_b", default="Sam")
    ap.add_argument("--n", type=int, default=1, help="stories to generate")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true", help="print ASP program")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.mystery:
        valid_ids = COMPATIBLE.get(args.setting, {}).get(args.mystery, [])
        if not valid_ids:
            raise StoryError(f"No compatible clues for {args.mystery} at {args.setting}.")

    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))

    # Choose clue subset that satisfies required_clues
    req = set(MYSTERIES[mystery].required_clues)
    pool_ids = COMPATIBLE[setting][mystery] if setting in COMPATIBLE and mystery in COMPATIBLE[setting] else []
    if not pool_ids:
        raise StoryError(f"The combination {setting}/{mystery} offers no compatible clues.")

    candidates = [cid for cid in pool_ids if cid in CLUES]
    selection = rng.sample(candidates, k=len(req)) if len(candidates) > len(req) else candidates

    sleuth_a = args.sleuth_a
    sleuth_b = args.sleuth_b
    return StoryParams(
        setting=setting,
        mystery=mystery,
        sleuth_a=sleuth_a,
        sleuth_b=sleuth_b,
        clue_pool=selection[:5],  # keep small for child audience
        seed=args.seed,
    )

def generate(params: StoryParams) -> StorySample:
    world = tell_story(
        params.setting,
        params.mystery,
        params.clue_pool,
        params.sleuth_a,
        params.sleuth_b,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print("\n---\nWorld state:\n", "\n ".join(f"{k}\n  {v}" for k,v in sample.world.facts.items()))
    if qa:
        print("\n\n---\nQ&A for curious detectives:\n")
        for q in sample.story_qa:
            print(f"Q: {q.question}\nA: {q.answer}\n")
        print("---\nWorld knowledge:\n")
        for q in sample.world_qa:
            print(f"Q: {q.question}\nA: {q.answer}\n")

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_swoon_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        stories = asp.atoms(asp.one_model(asp_program("#show valid_swoon_story/4.")), "valid_swoon_story")
        print(f"{len(stories)} detective duos ready:\n")
        for place, m, a, b in stories:
            print(f"  {place:15} / {m:20}  with {a}-{b}")
        return

    seed = args.seed or random.randrange(1<<30)
    rng = random.Random(seed)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(
            setting="mystery_lane", mystery="missing_note",
            sleuth_a="Alex", sleuth_b="Sam", clue_pool=["theater_ticket","love_note"]
        ))]
    else:
        for _ in range(args.n):
            try:
                params = resolve_params(args, rng)
                sample = generate(params)
                samples.append(sample)
            except StoryError as e:
                print(e)
                return

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2))
    else:
        for i, s in enumerate(samples):
            hdr = ""
            if args.all or len(samples) > 1:
                hdr = f"### Story {i+1}: {s.params.sleuth_a} & {s.params.sleuth_b} solve the {s.params.mystery}"
            emit(s, trace=args.trace, qa=args.qa, header=hdr)
            if i < len(samples)-1:
                print("\n"+"="*70)

if __name__ == "__main__":
    main()
