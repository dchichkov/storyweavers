#!/usr/bin/env python3
"""
A tiny storyworld for a rhyming tale about Carol, a pout, and a conflict
that turns into a thoughtful compromise.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
sys.path.insert(0, os.path.dirname(_storyworlds_dir))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    hero: str = "Carol"
    companion: str = "Mina"
    place: str = "the village hall"
    song: str = "the harvest carol"
    arc: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    params: StoryParams
    hero: Entity
    companion: Entity
    hall: Entity
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


HERO_NAMES = ["Carol", "Luna", "Tess", "Pia", "Nora", "Jules"]
COMPANION_NAMES = ["Mina", "Bea", "Owen", "Rafi", "Ivy", "Sam"]
PLACES = ["the village hall", "the apple-square stage", "the little schoolhouse"]
SONGS = ["the harvest carol", "the moonlit carol", "the lantern carol"]

ARCS = [
    {
        "premise": "Carol had practiced a bright carol for the village welcome night",
        "problem": "Mina wanted the song slow and gentle, while Carol wanted it quick and bouncy",
        "stake": "Their conflict could leave the waiting neighbors with no song at all",
        "pout": "Carol folded her arms and made a small, stubborn pout",
        "clue": "the youngest listeners softly hummed both rhythms at once",
        "action": "They tapped a calm beginning, then added a lively beat for the final verse",
        "twist": "the two tempos fit together like a breeze and a bell",
        "resolution": "Carol and Mina shared the melody, giving each singer a turn to lead",
        "lesson": "a conflict can become a harmony when every voice gets heard",
        "ending": "the last note floated over the square while Carol's pout melted into a smile",
        "question": "Why did Carol and Mina need to solve their disagreement?",
        "answer": "They needed to solve it so the villagers could enjoy the welcome-night song.",
    },
    {
        "premise": "Carol brought a basket of ribbons for a cheerful carol parade",
        "problem": "Carol chose blue ribbons, but Mina had promised red ones to the dancers",
        "stake": "The dancers might argue instead of marching together",
        "pout": "Carol puffed her cheeks and gave the basket a gloomy pout",
        "clue": "the red and blue ribbons made purple shadows in the afternoon sun",
        "action": "They braided one red ribbon with one blue ribbon for each dancer",
        "twist": "the braided colors made a pattern no single ribbon could show",
        "resolution": "They shared the ribbons and let each dancer choose a favorite side",
        "lesson": "different choices can make a brighter pattern when joined with care",
        "ending": "purple loops bobbed above the parade as the carol rang down the lane",
        "question": "How did Carol and Mina use the ribbons?",
        "answer": "They braided red and blue ribbons together so every dancer could wear both colors.",
    },
    {
        "premise": "Carol and Mina planned a carol beside a sleepy pond",
        "problem": "Carol wanted a loud drum, while Mina feared it would frighten the ducklings",
        "stake": "The music might disturb the small family they hoped to welcome",
        "pout": "Carol gave a disappointed pout beside the drum",
        "clue": "the ducklings stayed calm when the singers hummed softly",
        "action": "They replaced the drum with finger taps and quiet claps",
        "twist": "the ducklings began paddling in time with the gentle rhythm",
        "resolution": "Carol sang the high part while Mina kept the soft beat",
        "lesson": "careful listening can turn a noisy plan into a kinder one",
        "ending": "the ducklings made tiny ripples as the carol drifted across the pond",
        "question": "Why did Carol and Mina avoid the loud drum?",
        "answer": "They avoided it because the loud sound might frighten the ducklings.",
    },
    {
        "premise": "Carol found a golden bell for the winter carol",
        "problem": "Carol wanted to carry it first, but Mina had found it under the snow",
        "stake": "Their quarrel could hide the bell before the song began",
        "pout": "Carol's smile slipped into a round little pout",
        "clue": "the bell had two loops, one on each side",
        "action": "They held one loop each and walked together toward the singers",
        "twist": "the bell sounded clearest when both hands kept it steady",
        "resolution": "They took turns ringing it and thanked one another for the find",
        "lesson": "credit feels fair when the truth includes every helper",
        "ending": "the golden bell chimed between them, bright as frost in the morning sun",
        "question": "What helped Carol and Mina carry the bell together?",
        "answer": "The bell had two loops, so each friend could hold one side.",
    },
    {
        "premise": "Carol wrote a rhyming carol for the town's tiny garden",
        "problem": "Carol wanted every line to rhyme, while Mina wanted the words to tell a clear story",
        "stake": "The garden children might remember a pretty tune but miss its meaning",
        "pout": "Carol made a pout when Mina crossed out one of her fanciest lines",
        "clue": "the children repeated the simple lines and asked about the seeds",
        "action": "They kept the strong rhymes and added plain words about planting and rain",
        "twist": "the simplest verse became the one everyone could sing",
        "resolution": "Carol and Mina wrote the final verse together",
        "lesson": "beautiful words shine brightest when they also help others understand",
        "ending": "little voices sang the seed verse while green shoots nodded below",
        "question": "Why did Mina want some simpler words in the carol?",
        "answer": "Mina wanted simple words so the children could understand what the song meant.",
    },
]

OPENINGS = [
    "Morning bells bounced over the rooftops",
    "A rosy breeze skipped through the lane",
    "Sunlight sprinkled the windows with gold",
    "The town woke beneath a sky of blue",
    "Sparrows chirped above the busy square",
    "A warm wind carried the smell of bread",
]

THOUGHTS = [
    "'I want my way,' thought Carol, 'but a shared song may carry farther.'",
    "'A pout can show I am cross, but it cannot mend our plan,' Carol whispered to herself.",
    "'If I listen before I leap, perhaps a better beat will peep.'",
    "'Being right is not enough if our friends are left out of the song.'",
    "'Two ideas may clash like rain and sun, yet together they might make the music fun.'",
]

DIALOGUE = [
    ("Mina said, \"Carol, can you tell me what your part needs?\"", "Carol answered, \"I need a turn to make the song sparkle.\""),
    ("Carol asked, \"Mina, what are you worried might happen?\"", "Mina replied, \"I worry that our smallest listeners will be left behind.\""),
    ("Mina said, \"Let us test both ideas instead of guessing.\"", "Carol nodded. \"Then we can keep the part that helps everyone.\""),
    ("Carol asked, \"Could your plan fit with mine?\"", "Mina smiled. \"It can, if we make room for both.\""),
]

CODAS = [
    "Carol learned that listening can turn a pout into a proud smile.",
    "The friends discovered that a fair compromise can rhyme with surprise.",
    "From then on, they called their best songs 'together tunes.'",
    "Carol kept the lesson close: a shared voice can make a stronger choice.",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A rhyming conflict storyworld about Carol, a pout, and a shared carol."
    )
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--companion", choices=COMPANION_NAMES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--song", choices=SONGS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HERO_NAMES)
    companion = args.companion or rng.choice([n for n in COMPANION_NAMES if n != hero])
    place = args.place or rng.choice(PLACES)
    song = args.song or rng.choice(SONGS)
    if hero == companion:
        raise StoryError("The hero and companion must be different characters.")
    return StoryParams(
        hero=hero,
        companion=companion,
        place=place,
        song=song,
        arc=rng.randrange(len(ARCS)),
        seed=args.seed,
    )


def build_world(params: StoryParams) -> World:
    return World(
        params=params,
        hero=Entity(params.hero, "hero"),
        companion=Entity(params.companion, "companion"),
        hall=Entity(params.place, "place"),
    )


def simulate(world: World) -> None:
    p = world.params
    arc = ARCS[p.arc]
    rng = random.Random(p.seed)

    world.hero.memes["pride"] = 1.0
    world.hero.memes["pout"] = 1.0
    world.companion.memes["care"] = 1.0
    world.facts.update(
        problem=arc["problem"],
        stake=arc["stake"],
        clue=arc["clue"],
        song=p.song,
        place=p.place,
        resolved=False,
    )

    world.say(
        f"{rng.choice(OPENINGS)}. In {p.place}, {p.hero} and {p.companion} "
        f"prepared {p.song} with a bright, light, right little tune."
    )
    world.say(f"{arc['premise']}. They hoped the whole neighborhood would sing along.")
    world.para()

    world.say(f"But {arc['problem']}. {arc['stake']}.")
    world.say(f"{arc['pout']}. Her lips made a tiny cloud over the tune.")
    world.say(rng.choice(THOUGHTS))
    world.facts["pout_started"] = True

    world.para()
    first, second = rng.choice(DIALOGUE)
    world.say(f"{first} {second}")
    world.say(f"Together they noticed that {arc['clue']}.")
    world.say(f"{arc['action']}.")
    world.say(f"Then came the twist: {arc['twist']}.")
    world.hero.memes["pout"] = 0.0
    world.hero.memes["cooperation"] = 1.0
    world.companion.memes["cooperation"] = 1.0
    world.facts["solution"] = arc["action"]
    world.facts["twist"] = arc["twist"]

    world.para()
    world.say(f"{arc['resolution']}. {rng.choice(CODAS)}")
    world.say(f"As the evening settled, {arc['ending']}.")
    world.facts["resolved"] = True
    world.facts["ending"] = arc["ending"]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
    arc = ARCS[params.arc]
    prompts = [
        f"Write a rhyming story about {params.hero} and {params.companion} solving a conflict during {params.song}.",
        f"Tell a child-friendly tale in {params.place} where a pout changes into cooperation.",
        f"Create a gentle story about this conflict: {arc['problem']}.",
    ]
    story_qa = [
        QAItem(
            question=f"What caused the conflict between {params.hero} and {params.companion}?",
            answer=f"The conflict began because {arc['problem']}.",
        ),
        QAItem(
            question=f"Why did {params.hero} make a pout?",
            answer=f"{params.hero} made a pout because the disagreement frustrated her while {arc['stake'].lower()}",
        ),
        QAItem(
            question="What clue helped them find a solution?",
            answer=f"They noticed that {arc['clue']}.",
        ),
        QAItem(
            question="How did the friends solve the conflict?",
            answer=f"They solved it when {arc['action'].lower()}.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"The conflict became cooperation: {arc['resolution'].lower()}, and {arc['ending'].lower()}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a conflict?",
            answer="A conflict is a disagreement or problem between people who want different things.",
        ),
        QAItem(
            question="What is a pout?",
            answer="A pout is a small unhappy expression made with the lips when someone feels disappointed or cross.",
        ),
        QAItem(
            question="What is a carol?",
            answer="A carol is a song, often a cheerful one, that people sing together.",
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in [world.hero, world.companion, world.hall]:
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(f"  {ent.name:18} ({ent.kind:11}) meters={meters} memes={memes}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/1.
#show feature/1.
valid(story) :- domain(carol_pout), feature(conflict), feature(rhyming_story).
feature(conflict).
feature(rhyming_story).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("domain", "carol_pout"),
            asp.fact("character", "carol"),
            asp.fact("feature", "conflict"),
            asp.fact("feature", "rhyming_story"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/1."))
    if asp.atoms(model, "valid") == [("story",)]:
        for params in CURATED:
            sample = generate(params)
            if not sample.story or "Carol" not in sample.story:
                print("MISMATCH: generated story check failed.")
                return 1
        print("OK: ASP twin and generated stories are consistent.")
        return 0
    print("MISMATCH: ASP twin failed.")
    return 1


CURATED = [
    StoryParams(hero="Carol", companion="Mina", place="the village hall", song="the harvest carol", arc=0, seed=101),
    StoryParams(hero="Carol", companion="Bea", place="the apple-square stage", song="the lantern carol", arc=2, seed=202),
    StoryParams(hero="Luna", companion="Owen", place="the little schoolhouse", song="the moonlit carol", arc=4, seed=303),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print(asp_program("#show valid/1.\n#show feature/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/1.\n#show feature/1."))
        print(asp.atoms(model, "valid"))
        print(asp.atoms(model, "feature"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for i in range(max(args.n, 0)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
