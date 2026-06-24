#!/usr/bin/env python3
"""
Storyworld: aft_stance_mitt_foreshadowing_humor_sound_effects.py

A small pirate-tale story world with typed entities, physical meters, emotional
memes, causal state changes, a reasonableness gate, and an inline ASP twin.

Seed-inspired premise:
- A tiny pirate crew on a ship.
- One child keeps an aft stance while guarding a mitt-like treasure sack.
- Foreshadowing, humor, and sound effects shape the narrative.
- A surprise problem appears, then gets resolved by a practical pirate fix.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Theme:
    id: str
    scene: str
    rig: str
    ship_word: str
    aft_word: str
    goal: str
    send_off: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    where: str
    sound: str
    makes_problem: bool = False
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    the: str
    near: str
    flammable: bool = False
    spread: int = 0
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        return other


@dataclass
class StoryParams:
    theme: str
    tool: str
    problem: str
    response: str
    captain: str
    mate: str
    captain_gender: str
    mate_gender: str
    parent: str
    seed: Optional[int] = None


THEMES = {
    "pirates": Theme(
        id="pirates",
        scene="a swashbuckling island",
        rig="The stool was the crow's nest, a broom was the mast, and a crinkly mitt held their pretend gold.",
        ship_word="ship",
        aft_word="aft",
        goal="the hidden cove",
        send_off="sailed off laughing toward the cove",
    ),
    "harbor": Theme(
        id="harbor",
        scene="a busy harbor",
        rig="The couch was the dock, a cardboard box was the cargo hold, and a bright mitt guarded the treasure map.",
        ship_word="boat",
        aft_word="aft",
        goal="the lighthouse dock",
        send_off="drifted away to the lighthouse",
    ),
    "island": Theme(
        id="island",
        scene="a tiny island",
        rig="The blanket was the deck, a spoon became the oar, and a patched mitt kept the pearls safe.",
        ship_word="ship",
        aft_word="aft",
        goal="the sleepy reef",
        send_off="sailed out to the reef",
    ),
}

TOOLS = {
    "bucket": Tool(
        id="bucket",
        label="bucket",
        phrase="a little bucket of water",
        where="by the galley door",
        sound="Sploosh!",
        makes_problem=False,
        tags={"water"},
    ),
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a brass lantern",
        where="on the aft rail",
        sound="Click!",
        makes_problem=False,
        tags={"light"},
    ),
    "mitt": Tool(
        id="mitt",
        label="mitt",
        phrase="a mitt with a shiny patch",
        where="near the chest",
        sound="Fwip!",
        makes_problem=True,
        tags={"mitt", "humor"},
    ),
}

PROBLEMS = {
    "rope": Problem(
        id="rope",
        label="rope coil",
        the="the rope coil",
        near="the rope coil",
        flammable=True,
        spread=2,
        tags={"rope"},
    ),
    "sail": Problem(
        id="sail",
        label="sail",
        the="the sail",
        near="the sailcloth",
        flammable=True,
        spread=3,
        tags={"sail"},
    ),
    "crate": Problem(
        id="crate",
        label="crate of dry straw",
        the="the crate of dry straw",
        near="the dry straw",
        flammable=True,
        spread=2,
        tags={"crate"},
    ),
}

RESPONSES = {
    "water": Response(
        id="water",
        sense=3,
        power=3,
        text="grabbed the bucket and splashed the flames until they sizzled out",
        fail="splashed the bucket, but the fire was already too lively",
        qa_text="put the fire out with a bucket of water",
        tags={"water"},
    ),
    "blanket": Response(
        id="blanket",
        sense=3,
        power=2,
        text="yanked down a thick blanket and smothered the sparks",
        fail="tried to smother the sparks, but they skittered away",
        qa_text="smothered the sparks with a thick blanket",
        tags={"blanket"},
    ),
    "call_help": Response(
        id="call_help",
        sense=2,
        power=4,
        text="shouted for a grown-up and helped them bring the right gear",
        fail="shouted for help, but the flames beat the crew to it",
        qa_text="called a grown-up for help",
        tags={"help"},
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Pippa", "Zoe"]
BOY_NAMES = ["Finn", "Tom", "Jace", "Owen", "Ben"]


def hazard_at_risk(tool: Tool, problem: Problem) -> bool:
    return tool.makes_problem and problem.flammable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def fire_severity(problem: Problem) -> int:
    return problem.spread


def is_contained(response: Response, problem: Problem) -> bool:
    return response.power >= fire_severity(problem)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for th in THEMES:
        for tl in TOOLS:
            for pb in PROBLEMS:
                if hazard_at_risk(TOOLS[tl], PROBLEMS[pb]):
                    combos.append((th, tl, pb))
    return combos


def story_knowledge() -> dict[str, list[tuple[str, str]]]:
    return {
        "water": [("What does water do to a small fire?", "Water can cool a small fire and help put it out.")],
        "blanket": [("How does a blanket help with sparks?", "A thick blanket can smother small sparks by cutting off air.")],
        "help": [("What should you do if a fire starts?", "Get away and call a grown-up right away.")],
        "mitt": [("What is a mitt?", "A mitt is a soft hand covering or glove, and in stories it can also be a silly pretend treasure sack.")],
        "rope": [("Why can dry rope catch fire?", "Dry rope burns quickly, so flames can spread along it fast.")],
        "sail": [("Why is a sail risky near fire?", "A sail is cloth, and cloth can burn fast.")],
        "crate": [("Why can dry straw be dangerous near flames?", "Dry straw catches fire easily and can spread flames quickly.")],
    }


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _spread(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.meters.get("burning", 0) < THRESHOLD:
            continue
        sig = ("spread", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "deck" in world.entities:
            world.get("deck").meters["danger"] = world.get("deck").meters.get("danger", 0) + 1
        for ent in world.entities.values():
            if ent.kind == "character":
                ent.memes["fear"] = ent.memes.get("fear", 0) + 1
        out.append("crackle")
    return out


CAUSAL_RULES = [Rule("spread", _spread)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            res = rule.apply(world)
            if res:
                changed = True
                produced.extend(res)
    if narrate:
        for s in produced:
            if s == "crackle":
                world.say("Crackle-crackle! The flames licked along the deck.")
    return produced


def do_problem(world: World, problem: Problem) -> None:
    world.get("problem").meters["burning"] = 1
    propagate(world, narrate=True)


def make_story(theme: Theme, tool: Tool, problem: Problem, response: Response,
               captain: str, mate: str, captain_gender: str, mate_gender: str,
               parent: str) -> World:
    w = World()
    cap = w.add(Entity(id=captain, kind="character", type=captain_gender, role="captain", memes={"joy": 1, "stance": 1}))
    mat = w.add(Entity(id=mate, kind="character", type=mate_gender, role="mate", memes={"joy": 1}))
    par = w.add(Entity(id=parent, kind="character", type="mother" if parent == "Mum" else "father", role="parent"))
    deck = w.add(Entity(id="deck", kind="thing", type="deck", label="deck"))
    pr = w.add(Entity(id="problem", kind="thing", type=problem.id, label=problem.label))
    w.facts["theme"] = theme
    w.facts["tool"] = tool
    w.facts["problem_cfg"] = problem
    w.facts["response"] = response
    w.facts["captain"] = cap
    w.facts["mate"] = mat
    w.facts["parent"] = par

    cap.meters["aft"] = 1
    cap.meters["stance"] = 1
    cap.meters["mitt"] = 1
    w.say(f"On a sunny morning, {cap.id} and {mat.id} turned {theme.scene} into a game. {theme.rig}")
    w.say(f"{cap.id} kept an aft stance by the rear rail, because a pirate who watches the aft can spot trouble sooner.")

    # Foreshadowing + humor + sound effects
    w.para()
    w.say(f'"If I stand any stiffer, I might turn into a mast," {cap.id} joked.')
    w.say(f"{tool.sound} went the {tool.label} as {mat.id} bounced it once, and the silly mitt gave a little {tool.sound.lower()}.")
    w.say(f'But {mat.id} noticed {tool.phrase} sitting {tool.where} and said, "That looks useful... maybe too useful."')

    # Temptation
    w.para()
    if tool.makes_problem:
        cap.memes["curiosity"] = cap.memes.get("curiosity", 0) + 1
        w.say(f'"We need light near the aft," {cap.id} said. "What if we use {tool.label}?"')
        w.say(f'{mat.id} squinted. "That would be a very pirate way to make a problem."')
        w.say("The wind whispered over the deck, and the cracked lantern on the wall seemed to wink back.")
        w.say(f'"Ha!" {cap.id} grinned. "My stance is strong enough for any stunt."')
    else:
        w.say(f'{mat.id} chose the safer thing right away, and the aft stayed calm.')

    # Decision / problem
    if tool.makes_problem and hazard_at_risk(tool, problem):
        w.para()
        do_problem(w, problem)
        w.say(f'{tool.sound} went the tiny flame, and then -- whoosh! -- it touched {problem.near}.')
        w.say(f'The {problem.label} caught fast, because dry things and flames are bad neighbors.')
        w.say(f'"Aft!" yelled {mat.id}. "Fire!"')

        w.para()
        contained = is_contained(response, problem)
        if contained:
            w.say(f'{parent} came running and {response.text.replace("{target}", problem.label)}.')
            w.say("The crackle faded to a whisper, then to nothing.")
            w.say(f'{parent} shook {cap.id} and {mat.id} into a hug. "You did the right thing by calling me."')
            w.say(f'Both children learned that a brave stance means asking for help, not making a bigger flame.')
            w.para()
            w.say(f'The next day, {parent} handed them a lantern, and {cap.id} kept the aft stance just for play.')
            w.say(f'{mat.id} held the mitt high like a captain waving a flag. "Safe light!" they cheered.')
            outcome = "contained"
        else:
            w.say(f'{parent} came running and {response.fail.replace("{target}", problem.label)}.')
            w.say("The fire grew too fast for the small crew.")
            w.say(f'They escaped to the beach, coughing but safe, while the ship lost its silly deck game.')
            w.say(f'Afterward, they never forgot: fire is faster than a joke, and a grown-up must come first.')
            outcome = "burned"
    else:
        outcome = "averted"
        w.para()
        w.say(f'{mat.id} pointed at the aft rail and laughed. "A strong stance is good, but a smarter one is better."')
        w.say(f'{cap.id} nodded, put the {tool.label} back, and chose the lantern instead.')
        w.say(f'{tool.sound} went the safe lamp, bright and gentle.')
        w.say(f'The tiny crew sailed on toward {theme.goal}, still laughing at the idea of a mitt guarding treasure like a grumpy fish.')
        w.say(f'By sunset, they {theme.send_off} with no smoke at all.')

    w.facts["outcome"] = outcome
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    th, tl, pb, resp = f["theme"], f["tool"], f["problem_cfg"], f["response"]
    return [
        f"Write a pirate tale for a young child where {f['captain'].id} keeps an aft stance and a mitt is part of the game. Include humor, foreshadowing, and sound effects.",
        f"Tell a story where {f['captain'].id} and {f['mate'].id} play pirates, notice a risky {tl.label}, and something near {pb.the} catches fire.",
        f"Write a small swashbuckling story that starts playful, uses the word aft, and ends with a safer choice after a problem near {pb.the}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cap, mat, par = f["captain"], f["mate"], f["parent"]
    th, tl, pb, resp = f["theme"], f["tool"], f["problem_cfg"], f["response"]
    qa = [
        QAItem(
            question=f"What game did {cap.id} and {mat.id} play?",
            answer=f"They played pirates and turned {th.scene} into a pretend ship game.",
        ),
        QAItem(
            question=f"What did {cap.id} keep by the aft rail?",
            answer=f"{cap.id} kept an aft stance by the rear of the pretend ship, and the {tl.label} nearby was part of the foreshadowing.",
        ),
        QAItem(
            question=f"What sound did the {tl.label} make in the story?",
            answer=f"It went {tl.sound}, which added a funny sound effect to the pirate game.",
        ),
        QAItem(
            question=f"What problem could the {tl.label} cause near {pb.the}?",
            answer=f"It could make a flame, and that flame could catch {pb.the} because the problem was flammable.",
        ),
    ]
    if f["outcome"] == "contained":
        qa.append(QAItem(
            question=f"How did {par.id} stop the fire?",
            answer=f"{par.id} came running and {resp.qa_text}. That was enough to beat the small fire.",
        ))
    elif f["outcome"] == "burned":
        qa.append(QAItem(
            question=f"Could {par.id}'s response stop the fire?",
            answer=f"No. {par.id} tried, but the fire was already too big for that response.",
        ))
    else:
        qa.append(QAItem(
            question=f"What safer choice did the children make instead of using the risky tool?",
            answer=f"They put the {tl.label} away and used a lantern instead.",
        ))
    return qa


def world_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["tool"].tags) | set(world.facts["problem_cfg"].tags)
    out: list[QAItem] = []
    for tag, items in story_knowledge().items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("\n== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes} role={e.role}")
    return "\n".join(lines)


CURATED = [
    StoryParams("pirates", "mitt", "rope", "water", "Mina", "Tom", "girl", "boy", "Mom"),
    StoryParams("harbor", "mitt", "sail", "blanket", "Finn", "Lily", "boy", "girl", "Dad"),
    StoryParams("island", "mitt", "crate", "call_help", "Nora", "Jace", "girl", "boy", "Mum"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate storyworld with aft stance, mitt humor, and sound effects.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["Mom", "Dad", "Mum"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("That response is too weak for this storyworld.")
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.tool is None or c[1] == args.tool)
              and (args.problem is None or c[2] == args.problem)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    theme, tool, problem = rng.choice(combos)
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    girl = rng.choice(GIRL_NAMES)
    boy = rng.choice(BOY_NAMES)
    captain, captain_gender = rng.choice([(girl, "girl"), (boy, "boy")])
    mate, mate_gender = (boy, "boy") if captain_gender == "girl" else (girl, "girl")
    parent = args.parent or rng.choice(["Mom", "Dad", "Mum"])
    return StoryParams(theme, tool, problem, response, captain, mate, captain_gender, mate_gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = make_story(
        THEMES[params.theme],
        TOOLS[params.tool],
        PROBLEMS[params.problem],
        RESPONSES[params.response],
        params.captain,
        params.mate,
        params.captain_gender,
        params.mate_gender,
        params.parent,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
sense_min(2).
response_ok(R) :- response(R), sense(R,S), sense_min(M), S >= M.
hazard(T,L) :- makes_problem(T), flammable(L).
valid(T,Tool,Prob) :- theme(T), tool(Tool), problem(Prob), hazard(Tool, Prob).
contained :- chosen_response(R), power(R,P), severity(S), P >= S.
severity(S) :- chosen_problem(P), spread(P,S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.makes_problem:
            lines.append(asp.fact("makes_problem", tid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        if p.flammable:
            lines.append(asp.fact("flammable", pid))
        lines.append(asp.fact("spread", pid, p.spread))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show response_ok/1."))
    return sorted(x for (x,) in asp.atoms(model, "response_ok"))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("Mismatch in valid combos.")
    if set(asp_sensible()) != {r.id for r in sensible_responses()}:
        rc = 1
        print("Mismatch in sensible responses.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show response_ok/1."))
        return
    if args.asp:
        print("\n".join(f"{a}" for a in asp_valid_combos()))
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base + i))
            samples.append(generate(params))
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
