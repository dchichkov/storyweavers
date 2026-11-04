"""Combine authored attention, narrative preferences, and grammatical probability."""

from __future__ import annotations

from dataclasses import asdict
import math
import random

from .grammar import Derivation, Forest, Grammar, detokenize, expand
from .world import BY_NAME, Frame, Kernel, World, commit, frames, make_world


def softmax(logits: list[float], temperature: float = 1) -> list[float]:
    if not math.isfinite(temperature) or temperature <= 0:
        raise ValueError("temperature must be finite and positive")
    largest = max(logits)
    weights = [math.exp((value - largest) / temperature) for value in logits]
    return [value / sum(weights) for value in weights]


def score_frame(world: World, kernel: Kernel, *, attention: bool = True) -> dict:
    """Query/key matching over grounded fact tags, followed by weighted values.

    Query tags and coefficients are authored. Attention is normalized over
    matching facts, independently of the eventual event/word distributions.
    Recent-event rules read structured history, never the rendered sentences.
    """
    facts = world.facts_for_attention()
    matches = [(fact, len(set(kernel.query) & set(fact.tags))) for fact in facts]
    matches = [(fact, overlap) for fact, overlap in matches if overlap]
    weights = softmax([float(overlap) for _, overlap in matches]) if matches else []
    coefficients = dict(kernel.preferences)
    contributions = []
    for (fact, overlap), weight in zip(matches, weights):
        feature = fact.id.split(".")[-1]
        coefficient = coefficients.get(feature, 0)
        # Keep facts visible even when their effect is a guard rather than a score.
        contribution = 4 * weight * coefficient * fact.value if attention else 0.0
        contributions.append(dict(fact=fact.id, text=fact.text, key_tags=list(fact.tags),
                                  query_overlap=overlap, attention_weight=weight if attention else 0,
                                  value=fact.value, coefficient=coefficient, contribution=contribution))
    narrative = []
    if world.history:
        last = world.history[-1]["frame"]["kind"]
        if last == "attempt" and kernel.name in {"ask", "think"}:
            narrative.append(dict(rule="respond_to_failed_attempt", source=world.history[-1]["id"], score=1.3))
        if last == "ask" and kernel.name == "receive":
            narrative.append(dict(rule="answer_request_with_help", source=world.history[-1]["id"], score=0.4))
    if kernel.name == "want" and "attempted" in world.flags:
        narrative.append(dict(rule="avoid_late_goal_restatement", source=None, score=-2.0))
    total = kernel.base + sum(c["contribution"] for c in contributions) + sum(n["score"] for n in narrative)
    return dict(kernel=kernel.name, base=kernel.base, query=list(kernel.query),
                attention=contributions, narrative=narrative, logit=total)


def build_forest(world: World, *, tense: str = "past", attention: bool = True,
                 temperature: float = 1) -> Forest:
    candidates = frames(world)
    if not candidates:
        raise ValueError("world has ended or has no executable next event")
    evidence = {k.name: score_frame(world, k, attention=attention) for k, _ in candidates}
    event_probs = softmax([evidence[k.name]["logit"] for k, _ in candidates], temperature)
    grammar = Grammar(world, tense)
    derivations = []
    for (kernel, frame), probability in zip(candidates, event_probs):
        evidence[kernel.name]["prior_probability"] = probability
        for tokens, grammar_probability, rules in expand(grammar.for_frame(frame)):
            derivations.append(Derivation(tokens, probability * grammar_probability, frame, rules))
    return Forest(derivations, evidence)


def sample_sentence(world: World, rng: random.Random, *, tense: str = "past",
                    attention: bool = True, temperature: float = 1) -> dict:
    forest = build_forest(world, tense=tense, attention=attention, temperature=temperature)
    tokens, trace = (), []
    # Bounded grammar: use its actual longest derivation, never silently truncate.
    limit = max(len(d.tokens) for d in forest.derivations) + 1
    for _ in range(limit):
        prediction = forest.predict(tokens)
        choices = prediction["choices"]
        selected = rng.choices(choices, weights=[c["probability"] for c in choices], k=1)[0]
        prediction["selected"] = selected["word"]
        prediction["selected_probability"] = selected["probability"]
        trace.append(prediction)
        if selected["word"] == "<END>":
            break
        tokens += (selected["word"],)
    else:
        raise RuntimeError("grammar failed to finish within its finite support")
    posterior = forest.event_posterior(tokens)
    if not posterior:
        raise RuntimeError("sampled words have no executable semantic interpretation")
    # Marginalize surface ambiguity; choose a frame only after the sentence ends.
    frame = rng.choices(list(posterior), weights=list(posterior.values()), k=1)[0]
    sentence = detokenize(tokens)
    event = commit(world, frame, sentence)
    return dict(text=sentence, tokens=list(tokens), event_id=event["id"],
                frame=asdict(frame), word_count=sum(t[0].isalpha() for t in tokens),
                probability=math.prod(t["selected_probability"] for t in trace),
                event_evidence=forest.evidence, derivation_count=len(forest.derivations),
                word_trace=trace)


def generate(scenario: str = "rescue", seed: int = 0, *, tense: str = "past",
             attention: bool = True, temperature: float = 1,
             fear: float | None = None, care: float | None = None,
             max_sentences: int = 12) -> dict:
    world = make_world(scenario, seed, fear=fear, care=care)
    initial = world.to_dict()
    rng, sentences = random.Random(seed), []
    for _ in range(max_sentences):
        if world.finished:
            break
        sentences.append(sample_sentence(world, rng, tense=tense, attention=attention, temperature=temperature))
    if not world.finished:
        raise RuntimeError(f"story did not reach an ending in {max_sentences} sentences")
    return dict(scenario=scenario, seed=seed, tense=tense, attention=attention,
                temperature=temperature, initial_world=initial, final_world=world.to_dict(),
                story=" ".join(s["text"] for s in sentences), sentences=sentences,
                probability=math.prod(s["probability"] for s in sentences))


def advance(scenario: str, seed: int, count: int, **options) -> World:
    """Get a reproducible world at a sentence boundary for completion queries."""
    world = make_world(scenario, seed, fear=options.pop("fear", None), care=options.pop("care", None))
    rng = random.Random(seed)
    for _ in range(count):
        if world.finished:
            raise ValueError("requested position is beyond the story ending")
        sample_sentence(world, rng, **options)
    return world
