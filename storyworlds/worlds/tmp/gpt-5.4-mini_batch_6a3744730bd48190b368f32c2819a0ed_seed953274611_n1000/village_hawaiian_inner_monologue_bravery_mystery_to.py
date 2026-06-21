#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/village_hawaiian_inner_monologue_bravery_mystery_to.py
======================================================================================

A standalone story world for a tiny fairy-tale-like domain:

- a child in a village
- a small mystery to solve
- an inner monologue that changes bravery
- a gentle reveal ending in a warm, bright image

This world keeps the prose driven by simulated state rather than a frozen template.
"""

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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "aunt"}
        male = {"boy", "father", "man", "king", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class StoryParams:
    village: str
    mystery: str
    clue: str
    hero: str
    hero_gender: str
    companion: str
    companion_gender: str
    elder: str
    elder_gender: str
    ending: str
    seed: Optional[int] = None


@dataclass
class Village:
    id: str
    name: str
    setting: str
    mood: str
    secret_place: str
    light_place: str
    clue_place: str


@dataclass
class Mystery:
    id: str
    title: str
    question: str
    clue_kind: str
    reveal: str
    prompt: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    found_in: str
    helps: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Ending:
    id: str
    step: int
    solved: bool
    text: str
    fail_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.memes["worry"] >= THRESHOLD and hero.memes["resolve"] < THRESHOLD:
        sig = ("resolve", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["resolve"] += 1
            hero.memes["bravery"] += 1
            out.append("__resolve__")
    return out


def _r_solve(world: World) -> list[str]:
    out: list[str] = []
    if world.get("hero").memes["resolve"] < THRESHOLD:
        return out
    if world.get("clue").meters["found"] < THRESHOLD:
        return out
    if world.get("mystery").meters["solved"] < THRESHOLD:
        sig = ("solve", "mystery")
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("mystery").meters["solved"] += 1
            out.append("__solve__")
    return out


CAUSAL_RULES = [Rule("bravery", _r_bravery), Rule("solve", _r_solve)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World, clue_id: str) -> dict:
    sim = world.copy()
    sim.get(clue_id).meters["found"] += 1
    propagate(sim, narrate=False)
    return {
        "solved": sim.get("mystery").meters["solved"] >= THRESHOLD,
        "bravery": sim.get("hero").memes["bravery"],
    }


def tell(village: Village, mystery: Mystery, clue: Clue, ending: Ending,
         hero_name: str, hero_gender: str,
         companion_name: str, companion_gender: str,
         elder_name: str, elder_gender: str) -> World:
    w = World()
    hero = w.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    companion = w.add(Entity(id=companion_name, kind="character", type=companion_gender, role="companion"))
    elder = w.add(Entity(id=elder_name, kind="character", type=elder_gender, role="elder"))
    clue_ent = w.add(Entity(id="clue", kind="thing", type="thing", label=clue.label))
    mystery_ent = w.add(Entity(id="mystery", kind="thing", type="thing", label=mystery.title))
    w.facts.update(village=village, mystery=mystery, clue=clue, ending=ending,
                   hero=hero, companion=companion, elder=elder,
                   clue_ent=clue_ent, mystery_ent=mystery_ent)

    hero.memes["bravery"] = 0.0
    hero.memes["worry"] = 0.0
    companion.memes["hope"] = 1.0

    w.say(
        f"In the village of {village.name}, where the palms nodded and the sea "
        f"breathed like a lullaby, {hero.id} found a mystery to solve. "
        f"{village.setting}."
    )
    w.say(
        f'"{mystery.question}" {hero.id} wondered, and in {hero.pronoun("possessive")} '
        f"small quiet heart, {hero.id} listened to a careful inner voice."
    )

    w.para()
    hero.memes["worry"] += 1
    w.say(
        f'{hero.id} peeked toward {village.secret_place}. The air felt hushed. '
        f'"I can be brave," {hero.id} told {hero.pronoun("object")}self, '
        f'"even if my knees feel like little stones."'
    )
    if hero.memes["worry"] >= THRESHOLD:
        hero.memes["bravery"] += 1
        w.say(f"{companion.id} stayed close, and {companion.id} smiled so {hero.id} would not feel alone.")

    w.para()
    w.say(
        f"{hero.id} followed the soft hint of {clue.phrase} near {clue.found_in}. "
        f"The clue felt small, but it glimmered like a star in a shell."
    )
    hero.memes["curiosity"] += 1
    clue_ent.meters["found"] += 1
    pred = predict(w, clue_ent.id)
    w.facts["predicted"] = pred
    propagate(w, narrate=False)

    if ending.solved:
        w.say(
            f"When {hero.id} touched the clue, {mystery.reveal}."
        )
        w.say(
            f"{elder.id} nodded, proud and calm. '{ending.text}'"
        )
        hero.memes["joy"] += 1
        companion.memes["joy"] += 1
    else:
        w.say(
            f"Even so, the answer stayed hidden, and the village lanterns began "
            f"to wobble in the wind."
        )
        w.say(
            f"{elder.id} lifted a hand and pointed the way home. '{ending.fail_text}'"
        )

    w.para()
    w.say(
        f"By moonrise, {ending.qa_text}. The little mystery was no longer a mystery, "
        f"and {village.name} glowed softly under the hawaiian sky."
    )

    w.facts.update(
        solved=ending.solved,
        hero_brave=hero.memes["bravery"] >= THRESHOLD,
        clue_found=clue_ent.meters["found"] >= THRESHOLD,
    )
    return w


VILLAGES = {
    "harbor": Village(
        id="harbor",
        name="Mele Harbor",
        setting="The houses were painted in bright colors, and a tiny path led from the village square to the shore",
        mood="gentle",
        secret_place="the banyan tree",
        light_place="the lantern porch",
        clue_place="the shell path",
    ),
    "valley": Village(
        id="valley",
        name="Lani Valley",
        setting="The little homes rested between green hills, and every door had a flower wreath",
        mood="quiet",
        secret_place="the stone well",
        light_place="the moonlit bridge",
        clue_place="the fern lane",
    ),
}

MYSTERIES = {
    "song": Mystery(
        id="song",
        title="the missing song",
        question="Who was singing the old hawaiian song at night?",
        clue_kind="shell",
        reveal="the song came from a wind chime hidden in the banyan branches",
        prompt="a song that sounded like ocean bells",
        tags={"song", "hawaiian"},
    ),
    "lantern": Mystery(
        id="lantern",
        title="the hidden lantern",
        question="Who had tucked the little lantern away?",
        clue_kind="leaf",
        reveal="the lantern had been wrapped carefully in a leaf basket",
        prompt="a light that kept blinking on and off",
        tags={"lantern", "light"},
    ),
    "footprints": Mystery(
        id="footprints",
        title="the strange footprints",
        question="Where did the strange footprints come from?",
        clue_kind="sand",
        reveal="the footprints belonged to the elder's little dog, who was chasing a gecko",
        prompt="marks on the path after the rain",
        tags={"footprints", "path"},
    ),
}

CLUES = {
    "shell": Clue(id="shell", label="shell", phrase="a pale shell", found_in="the shell path", helps="hearsong", tags={"shell"}),
    "leaf": Clue(id="leaf", label="leaf basket", phrase="a woven leaf basket", found_in="the lantern porch", helps="light", tags={"leaf"}),
    "sand": Clue(id="sand", label="wet footprints", phrase="a row of wet footprints", found_in="the path", helps="trail", tags={"sand"}),
}

ENDINGS = {
    "solved": Ending(
        id="solved", step=1, solved=True,
        text="You looked with a brave heart, and the village answered.",
        fail_text="The night is not ready, but your brave heart still matters.",
        qa_text="the clue had led the hero to the answer, and everyone smiled",
        tags={"solved", "happy"},
    ),
    "unsolved": Ending(
        id="unsolved", step=0, solved=False,
        text="We can wait for morning, and we can try again.",
        fail_text="The mystery can rest until dawn, because your courage was real.",
        qa_text="the mystery waited for morning, but the hero had already grown braver",
        tags={"unsolved", "gentle"},
    ),
}

GIRL_NAMES = ["Lani", "Malia", "Nalu", "Leilani", "Koa"]
BOY_NAMES = ["Kai", "Noa", "Ikaika", "Milo", "Niko"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for v in VILLAGES:
        for m in MYSTERIES:
            c = CLUES[MYSTERIES[m].clue_kind]
            if c.helps:
                combos.append((v, m, c.id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale village mystery world with bravery and inner monologue.")
    ap.add_argument("--village", choices=VILLAGES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--companion")
    ap.add_argument("--companion-gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["girl", "boy"])
    ap.add_argument("--ending", choices=ENDINGS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.village is None or c[0] == args.village)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    village, mystery, clue = rng.choice(sorted(combos))
    ending = args.ending or rng.choice(list(ENDINGS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    companion_gender = args.companion_gender or ("boy" if hero_gender == "girl" else "girl")
    elder_gender = args.elder_gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hero_gender)
    companion = args.companion or _pick_name(rng, companion_gender)
    if companion == hero:
        companion = _pick_name(rng, companion_gender)
    elder = args.elder or _pick_name(rng, elder_gender)
    if elder in {hero, companion}:
        elder = _pick_name(rng, elder_gender)
    return StoryParams(
        village=village, mystery=mystery, clue=clue,
        hero=hero, hero_gender=hero_gender,
        companion=companion, companion_gender=companion_gender,
        elder=elder, elder_gender=elder_gender,
        ending=ending,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    v, m = f["village"], f["mystery"]
    return [
        f'Write a fairy tale story in a village with the words "village" and "hawaiian" about {m.question.lower()}',
        f"Tell a gentle mystery story where {f['hero'].id} has an inner monologue and learns bravery in {v.name}.",
        f"Write a child-friendly story about a hawaiian village, a small clue, and a brave heart finding an answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    village: Village = f["village"]
    mystery: Mystery = f["mystery"]
    clue: Clue = f["clue"]
    ending: Ending = f["ending"]
    items = [
        QAItem(
            question="What kind of story is this?",
            answer=f"It is a fairy-tale style mystery story set in {village.name}, a village with a hawaiian feeling. A child listens to an inner monologue, gathers courage, and tries to solve a small puzzle.",
        ),
        QAItem(
            question=f"What did {hero.id} think before acting?",
            answer=f"{hero.id} felt nervous at first, but the inner voice in {hero.id}'s mind said to keep going. That quiet thought helped turn worry into bravery.",
        ),
        QAItem(
            question=f"What solved the mystery?",
            answer=f"A small clue, {clue.phrase}, led to the answer. Once the clue was found, the mystery no longer stayed hidden.",
        ),
    ]
    if ending.solved:
        items.append(QAItem(
            question="How did the story end?",
            answer=f"It ended happily: the answer was found, and {village.name} felt calm and bright again. The hero's bravery mattered because it helped the search reach the truth.",
        ))
    else:
        items.append(QAItem(
            question="How did the story end?",
            answer=f"It ended gently, with the mystery waiting for morning instead of rushing. Even so, the hero was braver than before.",
        ))
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a village?",
            answer="A village is a small place where people live close together, with homes and paths nearby.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the hard thing even when you feel scared. It does not mean having no fear at all.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet talking someone hears inside their own mind. It can help them think, choose, and feel braver.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
reachable(hero) :- clue_found.
brave(hero) :- reachable(hero).
solved(mystery) :- brave(hero), clue_found.
"""

def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("world", "village"),
        asp.fact("feature", "inner_monologue"),
        asp.fact("feature", "bravery"),
        asp.fact("feature", "mystery"),
        asp.fact("keyword", "village"),
        asp.fact("keyword", "hawaiian"),
    ])


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show world/1."))
    return sorted(set(asp.atoms(model, "world")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid()) != {("village",)}:
        print("MISMATCH: ASP twin did not produce the expected base world.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as err:
        print(f"MISMATCH: smoke test failed: {err}")
        rc = 1
    else:
        print("OK: ASP twin and smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    village = VILLAGES.get(params.village)
    mystery = MYSTERIES.get(params.mystery)
    clue = CLUES.get(params.clue)
    ending = ENDINGS.get(params.ending)
    if not village or not mystery or not clue or not ending:
        raise StoryError("invalid story parameters")

    world = tell(
        village=village, mystery=mystery, clue=clue, ending=ending,
        hero_name=params.hero, hero_gender=params.hero_gender,
        companion_name=params.companion, companion_gender=params.companion_gender,
        elder_name=params.elder, elder_gender=params.elder_gender,
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
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(village="harbor", mystery="song", clue="shell", hero="Lani", hero_gender="girl",
                companion="Kai", companion_gender="boy", elder="Auntie", elder_gender="girl", ending="solved"),
    StoryParams(village="valley", mystery="footprints", clue="sand", hero="Milo", hero_gender="boy",
                companion="Nalu", companion_gender="girl", elder="Uncle", elder_gender="boy", ending="unsolved"),
    StoryParams(village="harbor", mystery="lantern", clue="leaf", hero="Koa", hero_gender="boy",
                companion="Malia", companion_gender="girl", elder="Grandma", elder_gender="girl", ending="solved"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show world/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP world facts:")
        for atom in asp_valid():
            print(" ", atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
