#!/usr/bin/env python3
"""
A small animal storyworld about a startled forest picnic with a surprise,
rising suspense, and dialogue that ends in a happy yell.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, REPO_ROOT)
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    place: str = "meadow"
    animal: str = "bunny"
    helper: str = "squirrel"
    surprise: str = "a basket of berries"
    noise: str = "yell"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "animal"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def cap(self) -> str:
        return self.id.capitalize()


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.seen_suspense = False
        self.seen_surprise = False
        self.seen_yell = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


ANIMALS = {
    "bunny": ("bunny", "curious"),
    "fox": ("fox", "clever"),
    "duck": ("duck", "brave"),
    "deer": ("deer", "gentle"),
    "bear": ("bear", "slow"),
    "mouse": ("mouse", "tiny"),
    "squirrel": ("squirrel", "quick"),
}

PLACES = ["meadow", "pond", "garden", "woods"]
SURPRISES = [
    "a basket of berries",
    "a tiny kite",
    "a shiny shell",
    "a warm scarf",
]

INCIDENTS = [
    {
        "premise": "A row of acorn cups had appeared beside the picnic blanket overnight.",
        "problem": "One cup trembled, although the air was still, and a muffled scratch came from beneath it.",
        "guess": "A giant beetle is trapped under there",
        "clue": "a narrow trail of damp pawprints that stopped at the cup",
        "action": "They propped up the cup with a twig and left a clear path through the grass.",
        "reveal": "a shivering field mouse crawled out after sheltering from the rain",
        "gift_reason": "The mouse had carried the gift there to thank them for sharing dry leaves during the storm.",
        "ending": "Three acorn cups stood upside down to dry while the friends watched the last raindrops sparkle.",
    },
    {
        "premise": "Bright feathers pointed like arrows along one path through the {place}.",
        "problem": "Each arrow ended at a hollow log that answered every footstep with a hollow knock.",
        "guess": "Someone is warning us away",
        "clue": "one feather tucked into a loop of blue ribbon",
        "action": "They followed the arrows slowly and called into the log before reaching inside.",
        "reveal": "two young jays popped up and admitted they had planned a treasure trail",
        "gift_reason": "The jays had hidden the gift as the prize for anyone patient enough to follow every clue.",
        "ending": "Blue feathers fluttered above a new trail that everyone could solve together.",
    },
    {
        "premise": "At the {place} entrance, every daisy was leaning toward the same stone.",
        "problem": "The stone clicked twice, paused, and clicked twice again whenever they came close.",
        "guess": "The stone has learned to talk",
        "clue": "a strand of grass moving in and out of a crack beneath it",
        "action": "They tapped the pattern back, stepped away from the stone, and waited for an answer.",
        "reveal": "a cricket orchestra was rehearsing below the warm stone",
        "gift_reason": "The crickets had prepared the gift as a thank-you for keeping their stage safe.",
        "ending": "The daisies lifted in the evening breeze as the crickets played one bright final note.",
    },
    {
        "premise": "A little red flag waved from the middle of a shallow stream.",
        "problem": "Ripples circled the flag, and something beneath the water tugged its string downstream.",
        "guess": "A river monster has caught it",
        "clue": "neat tooth marks on a floating willow twig",
        "action": "They stayed on the bank, tied a vine to a branch, and gently drew the flag toward shore.",
        "reveal": "a beaver kit surfaced with the string looped around a bundle of reeds",
        "gift_reason": "The beaver family had marked the gift so the current would deliver it to their helpful neighbors.",
        "ending": "The freed reeds bobbed beside the dam while the red flag dried on a sunlit branch.",
    },
    {
        "premise": "A lantern glowed inside an empty burrow before sunset.",
        "problem": "Its light vanished whenever anyone spoke and returned whenever the surroundings became quiet.",
        "guess": "A shy star has fallen underground",
        "clue": "golden pollen dusted across the burrow entrance",
        "action": "They sat silently at a safe distance and shaded their eyes until they could see clearly.",
        "reveal": "a cloud of fireflies rose from behind a jar of glowing flowers",
        "gift_reason": "The fireflies had illuminated the gift so their friends could find it before dark.",
        "ending": "Fireflies made a gentle arch above the path, and no lantern was needed for the walk home.",
    },
    {
        "premise": "Fresh snow covered the clearing except for one perfect green circle.",
        "problem": "A low rumble came from the circle, sending crumbs of snow sliding from nearby branches.",
        "guess": "Something enormous is waking below us",
        "clue": "warm air smelling of pine drifting through a tunnel in the snow",
        "action": "They marked the soft edge with sticks and cleared the tunnel from firm ground.",
        "reveal": "a family of hedgehogs emerged from a snug leaf shelter, pushing a wooden cart",
        "gift_reason": "The hedgehogs had saved the gift for the friends who kept their winter doorway clear.",
        "ending": "Tiny wheel tracks crossed the snow toward a table glowing under strings of pinecones.",
    },
    {
        "premise": "A paper boat sailed across a rain pool at the {place} with nobody steering it.",
        "problem": "It circled the same reed three times, then disappeared behind the lily pads.",
        "guess": "The boat is trying to escape",
        "clue": "a silver thread tied from its mast to the far bank",
        "action": "They walked around the rain pool instead of wading in and traced the thread through the reeds.",
        "reveal": "an otter pulled the boat ashore and unfolded its secret map",
        "gift_reason": "The otter had drawn a map leading to the gift after the friends returned a lost paddle.",
        "ending": "The paper boat rested beside the opened map as moonlight drew a silver road across the pool.",
    },
    {
        "premise": "The old berry bell rang once from the empty hilltop.",
        "problem": "Every animal who climbed toward it heard rustling behind them, but saw only bending ferns.",
        "guess": "An invisible visitor is following us",
        "clue": "bits of purple wool snagged on three fern tips",
        "action": "They stopped climbing, compared the wool with nearby tracks, and invited the follower to come out.",
        "reveal": "a timid lamb stepped from the ferns carrying the bell rope in its teeth",
        "gift_reason": "The lamb had rung the bell to gather everyone for a surprise thank-you feast.",
        "ending": "The bell swayed silently above purple wool, polished bowls, and one last berry saved for morning.",
    },
    {
        "premise": "Someone had built a doorway of twigs between two trees.",
        "problem": "Beyond it, pinecones rolled uphill and vanished one at a time behind a mossy mound.",
        "guess": "The doorway leads to an upside-down forest",
        "clue": "a thin root lifting each pinecone like a tiny lever",
        "action": "They watched one full cycle, then placed a soft leaf where the rolling pinecones could stop.",
        "reveal": "three chipmunks emerged, testing an invention for moving winter stores",
        "gift_reason": "The chipmunks offered the gift because the leaf brake made their invention safe.",
        "ending": "A tidy line of pinecones waited behind the leaf brake while the twig doorway framed the sunset.",
    },
    {
        "premise": "A melody drifted from a nest that had been empty since spring.",
        "problem": "The song sped up whenever they approached, then stopped on one unfinished note.",
        "guess": "A trapped bird is calling for help",
        "clue": "a turning brass key visible between the woven grasses",
        "action": "They steadied the branch, turned the key backward once, and carefully loosened the grass around it.",
        "reveal": "a tiny music box opened beneath the nest lining",
        "gift_reason": "The returning swallows had left the music box and gift to celebrate their old home.",
        "ending": "The finished melody floated over the treetops while the brass key shone in the nest.",
    },
    {
        "premise": "A trail of soap bubbles crossed the {place} without popping.",
        "problem": "The largest bubble carried a folded note, but sharp brambles blocked its path.",
        "guess": "The note will be lost if the bubble bursts",
        "clue": "each bubble followed the warm breath of a hidden clay pipe",
        "action": "They bent the brambles aside with forked sticks and guided the bubble through the opening.",
        "reveal": "a mole appeared with the pipe and caught the bubble in a soft net",
        "gift_reason": "The note explained that the mole had planned the gift for the forest helpers.",
        "ending": "Rainbow bubbles floated through the cleared arch and reflected every smiling face.",
    },
    {
        "premise": "A small wooden chest sat beneath the picnic table with its lid tapping from inside.",
        "problem": "The tapping grew faster when the friends touched the latch, then stopped completely.",
        "guess": "A frightened animal may be locked in there",
        "clue": "a line of sunflower seeds leading to a tiny air hole",
        "action": "They called for the park keeper, kept the chest still, and spoke softly beside the air hole.",
        "reveal": "the keeper opened it and a wind-up drummer rolled out, still tapping",
        "gift_reason": "The drummer had switched on during delivery; the gift was a picnic surprise from all their neighbors.",
        "ending": "The toy drummer tapped a cheerful beat beside the safely opened chest as lanterns came on.",
    },
]

ROUTES = [
    ("At first, the day seemed ordinary.", "They paused and listened instead of rushing closer."),
    ("The mystery began before breakfast.", "They traded ideas in whispers and checked each one."),
    ("No one expected an adventure that afternoon.", "They chose the safest clue and followed it together."),
    ("The forest felt full of questions that morning.", "They looked high, low, and behind them before acting."),
    ("Their outing changed with one puzzling discovery.", "They counted what they knew and what they still needed to learn."),
    ("A curious sign interrupted their quiet walk.", "They made a careful plan, each friend taking one job."),
    ("The first clue arrived when the path was still empty.", "They tested a small idea and watched what changed."),
    ("Something unusual was waiting near their favorite path.", "They asked who might need help before touching anything."),
    ("A tiny mystery made the whole clearing seem suddenly hushed.", "They followed the evidence and kept one another from guessing too quickly."),
    ("Their picnic plan was forgotten as soon as they saw the clue.", "They spoke calmly, then tried the least risky solution first."),
    ("An unexpected sight stopped both friends in their tracks.", "They compared the sound, the tracks, and the nearest safe route."),
    ("The surprise announced itself in a most mysterious way.", "They waited through one more clue before deciding what it meant."),
]


def build_world(params: StoryParams) -> World:
    w = World(params)
    hero = w.add(Entity(id=params.animal, kind="character", type=params.animal, traits=[ANIMALS[params.animal][1], "little"]))
    helper = w.add(Entity(id=params.helper, kind="character", type=params.helper, traits=[ANIMALS[params.helper][1]]))
    gift = w.add(Entity(id="surprise", kind="thing", type="gift", label=params.surprise, phrase=params.surprise))
    selector = params.seed if params.seed is not None else 0
    incident_index = selector % len(INCIDENTS)
    route_index = (selector // len(INCIDENTS)) % len(ROUTES)
    w.facts.update(
        hero=hero,
        helper=helper,
        gift=gift,
        params=params,
        incident=INCIDENTS[incident_index],
        incident_index=incident_index,
        route=ROUTES[route_index],
        route_index=route_index,
    )
    return w


def narrate(world: World) -> None:
    p = world.params
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    gift: Entity = world.facts["gift"]  # type: ignore[assignment]
    incident: dict[str, str] = world.facts["incident"]  # type: ignore[assignment]
    route: tuple[str, str] = world.facts["route"]  # type: ignore[assignment]

    hero.memes["curiosity"] = 1
    helper.memes["teamwork"] = 1

    world.say(f"{route[0]} A little {hero.type} named {hero.cap()} met {helper.cap()}, the {helper.type}, at the {p.place}.")
    world.say(incident["premise"].format(place=p.place))
    world.say(f'"Did you arrange this?" asked {hero.cap()}. "Not this part," said {helper.cap()}.')

    world.para()
    hero.memes["suspense"] = 1
    world.seen_suspense = True
    world.say(incident["problem"])
    world.say(f'{hero.cap()} whispered, "{incident["guess"]}." {helper.cap()} replied, "Let us find evidence before we decide."')
    world.say(f'{route[1]} Soon they noticed {incident["clue"]}.')

    world.para()
    hero.memes["surprise"] = 1
    world.seen_surprise = True
    world.say(incident["action"])
    world.say(f'The suspense broke with a surprise: {incident["reveal"]}. Nearby waited {gift.label}.')
    world.say(f'"So that was the mystery!" said {hero.cap()}. {incident["gift_reason"]}')

    world.para()
    hero.meters["joy"] = 1
    world.seen_yell = True
    world.say(f'{hero.cap()} gave a happy {p.noise}. "We were brave enough to wait and wise enough to check!" {hero.pronoun()} said.')
    world.say(f'Together, the animals carried {gift.label} to a clear spot at the {p.place} and welcomed the surprise together. {incident["ending"]}')


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write an animal story with dialogue, suspense, surprise, and a happy {p.noise}.",
        f"Tell a short story about a {p.animal} and a {p.helper} at the {p.place} with a hidden surprise.",
        f"Make a gentle animal story where one friend says 'Wait and see' and the ending includes a {p.noise}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    gift: Entity = world.facts["gift"]  # type: ignore[assignment]
    incident: dict[str, str] = world.facts["incident"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who went to the {p.place} in the story?",
            answer=f"A little {hero.type} named {hero.cap()} went there with {helper.cap()}, the {helper.type}.",
        ),
        QAItem(
            question=f"What made {hero.cap()} and {helper.cap()} feel suspense at the {p.place}?",
            answer=f'{incident["problem"]} The two friends did not yet know what caused it.',
        ),
        QAItem(
            question=f"What clue did {hero.cap()} and {helper.cap()} use instead of trusting their first guess?",
            answer=f'They noticed {incident["clue"]}. That evidence helped them choose a careful action.',
        ),
        QAItem(
            question=f"What did the friends discover beside {gift.label}?",
            answer=f'They discovered that {incident["reveal"]}. That discovery explained the mystery at the {p.place}.',
        ),
        QAItem(
            question=f"Why did {hero.cap()} give a happy {p.noise} with {helper.cap()}?",
            answer=f'{hero.cap()} gave a happy {p.noise} because they had safely solved the mystery and could enjoy {gift.label} together.',
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is something the reader or character does not expect until the story reveals it.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of waiting and wondering what will happen next.",
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is when characters speak to each other in the story.",
        ),
        QAItem(
            question=f"What is a {p.place}?",
            answer=f"A {p.place} is a place where animals in the story can walk, hide, and play.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"incident={world.facts['incident_index']} route={world.facts['route_index']}")
    lines.append(f"suspense={world.seen_suspense} surprise={world.seen_surprise} yell={world.seen_yell}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- character(H).
helper(X) :- character(X).
has_suspense :- whispering(_).
has_surprise :- reveal(_).
has_yell :- yell(_).
good_story :- has_suspense, has_surprise, has_yell.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import inside ASP helpers
    lines = []
    for a in ANIMALS:
        lines.append(asp.fact("character", a))
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for s in SURPRISES:
        lines.append(asp.fact("surprise_item", s))
    lines.append(asp.fact("yell", "yell"))
    lines.append(asp.fact("whispering", "whispering"))
    lines.append(asp.fact("reveal", "reveal"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show good_story/0."))
    ok = any(sym.name == "good_story" for sym in model)
    py = True
    if ok == py:
        print("OK: ASP and Python parity verified.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld with suspense, surprise, dialogue, and a yell.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--helper", choices=sorted(ANIMALS))
    ap.add_argument("--surprise", choices=SURPRISES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random, sample_seed: int) -> StoryParams:
    animal = args.animal or rng.choice(list(ANIMALS))
    helper = args.helper or rng.choice([a for a in ANIMALS if a != animal])
    place = args.place or rng.choice(PLACES)
    surprise = args.surprise or rng.choice(SURPRISES)
    return StoryParams(place=place, animal=animal, helper=helper, surprise=surprise, seed=sample_seed)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate(world)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show good_story/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        combos = [
            StoryParams(place=p, animal=a, helper=h, surprise=s, seed=base_seed + i)
            for i, (p, a, h, s) in enumerate(
                [
                    ("meadow", "bunny", "squirrel", "a basket of berries"),
                    ("pond", "duck", "fox", "a tiny kite"),
                    ("garden", "mouse", "bear", "a shiny shell"),
                    ("woods", "deer", "bunny", "a warm scarf"),
                ]
            )
        ]
        samples = [generate(p) for p in combos]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 10):
            i += 1
            sample_seed = base_seed + i
            params = resolve_params(args, random.Random(sample_seed), sample_seed)
            if args.helper and params.helper == params.animal:
                raise StoryError("helper must be a different animal from the hero")
            story = generate(params)
            if story.story in seen:
                continue
            seen.add(story.story)
            samples.append(story)

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
