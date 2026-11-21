"""Sample words (including speech punctuation); commit every physical event.

Unnarrated operations have an empty surface and an END transition. They retain
their original probability, guards, effects and history entry. This is semantic
content selection, never deletion or rewriting of generated prose.
"""
from dataclasses import asdict
import hashlib
import math
import random

from ..engine import score_frame, softmax
from ..grammar import Derivation, Forest, expand, text
from ..world import Frame
from ..portable.runtime import setup as portable_setup
from . import library_world, pottery_world, rescue_world, kite_world, key_world, music_world, greenhouse_world
from .plans import plan
from .surface import detokenize

LEGACY_SCENARIOS = ("rescue", "kite", "key", "music", "greenhouse", "library", "pottery")
from .seed_worlds.engine import NAMES as NEW_SEED_SCENARIOS
SCENARIOS = LEGACY_SCENARIOS + NEW_SEED_SCENARIOS


def setup(scenario, seed=0, **options):
    edition=options.pop('edition','original')
    if edition=='crafted':
        from .revisions import pack
        unsupported=set(options)-{'choice','care','pride'}
        if unsupported:raise ValueError('crafted edition does not support: '+', '.join(sorted(unsupported)))
        p=pack(scenario)
        return p,p.make_world(seed,**options)
    if edition!='original':raise ValueError('unknown story edition')
    if 'beat_budget' in options:
        from ..beat_generation import initialize
        budget=options.pop('beat_budget')
        pack,world=setup(scenario,seed,**options)
        initialize(world,budget)
        return pack,world
    if options.pop('plot_annotations', False):
        from ..plot_annotations import PlotPack
        pack, world = setup(scenario, seed, **options)
        return PlotPack(pack), world
    if options.pop('multiscale', False):
        from ..event_scales import ScalePack, initialize
        pack, world = setup(scenario, seed, **options)
        initialize(pack, world, seed)
        return ScalePack(pack), world
    if scenario == "joined":
        from ..memory_transfer import setup_joined
        return setup_joined(**options)
    if scenario in NEW_SEED_SCENARIOS:
        from .seed_worlds.engine import pack
        p = pack(scenario)
        return p, p.make_world(seed, **options)
    if scenario == "rescue":
        return rescue_world, rescue_world.make_world(seed, **options)
    if scenario == "kite":
        return kite_world, kite_world.make_world(seed, **options)
    if scenario == "key":
        return key_world, key_world.make_world(seed, **options)
    if scenario == "music":
        return music_world, music_world.make_world(seed, **options)
    if scenario == "greenhouse":
        return greenhouse_world, greenhouse_world.make_world(seed, **options)
    if scenario in {"library", "pottery"}:
        pack = library_world if scenario == "library" else pottery_world
        return pack, pack.make_world(seed, **options)
    return portable_setup("heldout" if scenario == "greenhouse" else scenario, seed, **options)


def build_forest(pack, world, tense="past", *, attention=True, temperature=1, continuations="original", predict_attributes=False):
    before = world.to_dict()
    available = pack.candidates(world)
    if not available:
        raise ValueError("no available event")
    evidence = [score_frame(world, k, attention=attention) for k, _ in available]
    priors = softmax([e["logit"] for e in evidence], temperature)
    rows, scenes, annotations, endings = [], {}, [], []
    from .attribute_grammar import expand_attributes, candidate_attributes
    from .attribute_sampler import AttributeForest
    for (kernel, f), prior, item in zip(available, priors, evidence):
        rendered = (pack.render_scene(world, f, tense, continuations=continuations)
                    if hasattr(pack, "render_scene") else
                    plan(world, f, tense, getattr(pack, "LEXICON", None), continuations=continuations))
        if 'beats' in world.narrative:
            from ..beat_generation import expand_scene
            from .subject_coherence import cohere_scene
            rendered=expand_scene(pack,world,f,rendered,tense)
            rendered=cohere_scene(rendered)
        scenes[f] = rendered
        node = rendered.node if rendered else text("")
        annotated_branches = list(expand_attributes(node)) if predict_attributes else None
        branches = [(words, p, rules) for words, p, rules, _ in annotated_branches] if predict_attributes else list(expand(node))
        if not 0 < len(branches) <= 512 or not math.isclose(sum(p for _, p, _ in branches), 1, abs_tol=1e-9):
            raise AssertionError("unnormalized or oversized grammar")
        for index, (tokens, probability, labels) in enumerate(branches):
            rows.append(Derivation(tokens, prior * probability, f, labels))
            if predict_attributes:
                attrs = candidate_attributes(tokens, annotated_branches[index][3], f, world, kernel, before["entities"])
                if hasattr(pack, 'scale_context'):
                    context = pack.scale_context(world, f)
                    attrs = tuple({**a, 'event_scales': context} for a in attrs)
                annotations.append(attrs)
                ending = dict(pos='END', event=dict(name=f.kind.replace('_', ' '),
                    source_kind=f.kind, status='proposed', scope='candidate_scene',
                    roles={key: getattr(f,key) for key in ('actor','patient','instrument','destination') if getattr(f,key)}))
                if hasattr(pack, 'scale_context'):
                    ending['event_scales'] = context
                if hasattr(pack, 'plot_context'):
                    plot = pack.plot_context(world, f)
                    if plot is not None:
                        annotations[-1] = tuple({**a, 'plot': plot} for a in attrs)
                        ending['plot'] = plot
                if hasattr(pack,'narrative_context'):
                    context=pack.narrative_context(world,f)
                    annotations[-1]=tuple({**a,'storycraft':context} for a in annotations[-1])
                    ending['storycraft']=context
                endings.append(ending)
        item.update(frame=asdict(f), prior_probability=prior)
    assert before == world.to_dict(), "prediction mutated state"
    evidence = {str(i): e for i, e in enumerate(evidence)}
    return (AttributeForest(rows, evidence, annotations, end_annotations=endings) if predict_attributes else Forest(rows, evidence)), scenes


def generate(scenario="music", seed=7, *, tense="past", attention=True, temperature=1,
             symbolic_heads=False, head_profile="manual", head_strength=1.0,
             head_ids=None, continuations="original", token_annotations=False,
             predict_attributes=True, presentation=True, **options):
    if scenario not in (*SCENARIOS, "joined") or tense not in {"past", "present"}:
        raise ValueError("unknown scenario or tense")
    pack, w = setup(scenario, seed, **options)
    from .head_adapter import StoryHeads
    heads = StoryHeads(w, profile=head_profile, strength=head_strength, head_ids=head_ids) if symbolic_heads else None
    from .token_annotations import TokenAnnotations
    annotations = TokenAnnotations() if token_annotations else None
    initial = w.to_dict()
    rng, scenes, traces = random.Random(seed), [], []
    offset = 0
    attribute_stream = []
    from ..symbolic_heads.positions import Position, SymbolicRotary
    rotary = SymbolicRotary()
    sentence_index = local_position = 0
    pending_boundary = False
    generation_namespace = hashlib.sha256(repr((scenario, seed, tense, attention, temperature,
        symbolic_heads, head_profile, head_strength, head_ids, continuations, sorted(options.items()))).encode()).hexdigest()
    event_limit = getattr(pack, "event_limit", 32)
    for _ in range(event_limit):
        if w.finished:
            break
        forest, plans = build_forest(pack, w, tense, attention=attention, temperature=temperature,
                                    continuations=continuations, predict_attributes=predict_attributes)
        available = pack.candidates(w) if heads else None
        tokens, trace = (), []
        for _ in range(max(len(d.tokens) for d in forest.derivations) + 1):
            prediction = (heads.predict(forest, tokens, w, tense=tense, available=available)
                          if heads else forest.predict(tokens))
            if predict_attributes:
                forest.reconcile_word_weights(prediction)
            choices = prediction["choices"]
            assert math.isclose(sum(c["probability"] for c in choices), 1, abs_tol=1e-9)
            chosen = rng.choices(choices, weights=[c["probability"] for c in choices])[0]
            prediction.update(selected=chosen["word"], selected_probability=chosen["probability"])
            if predict_attributes:
                posterior_attributes = forest.observe(chosen["word"], prediction)
                prediction["selected_attributes"] = posterior_attributes
                if chosen["word"] != "<END>":
                    if pending_boundary and chosen["word"] not in {"”", '"', ".", "!", "?"}:
                        sentence_index += 1
                        local_position = 0
                        pending_boundary = False
                    position = Position(generation_namespace, len(attribute_stream), sentence_index, local_position)
                    attribute_stream.append(dict(token=chosen["word"], position=asdict(position),
                        rotary=rotary.encode(position), scene_index=len(traces),
                        candidates=posterior_attributes))
                    local_position += 1
                    if chosen["word"] in {".", "!", "?"}:
                        pending_boundary = True
            trace.append(prediction)
            if chosen["word"] == "<END>":
                break
            tokens += (chosen["word"],)
        else:
            raise AssertionError("word sampling did not finish")
        posterior = forest.event_posterior(tokens)
        # Head factors depend only on the observed prefix and committed world,
        # so every derivation of this text receives the same product of factors.
        # They cancel in the conditional posterior over its possible frames.
        frame = rng.choices(list(posterior), weights=list(posterior.values()))[0]
        matches = [d for d in forest.derivations if d.frame == frame and d.tokens == tokens]
        labels = sorted(set.intersection(*(set(d.rules) for d in matches)))
        expected = sum(d.probability for d in forest.derivations if d.tokens == tokens)
        probability = math.prod(p["selected_probability"] for p in trace)
        if not heads or head_strength == 0:
            assert math.isclose(probability, expected, rel_tol=1e-8)
        prose = detokenize(tokens)
        before_entities = w.to_dict()["entities"] if annotations is not None else None
        beat_decision=None
        if 'beats' in w.narrative:
            from ..beat_generation import select
            beat_decision=select(pack,w,frame,labels,tense)
        event = pack.commit(w, frame, prose)
        if 'beats' in w.narrative:
            from ..beat_generation import commit as commit_beats
            commit_beats(pack,w,event,beat_decision)
        if annotations is not None:
            annotations.append(plans[frame].node if plans[frame] else None, tokens, frame,
                               before_entities, w.to_dict()["entities"], event["id"])
        event["referents"] = sorted({r.split(":", 1)[1] for r in labels if r.startswith("referent:")})
        event["speakers"] = sorted({r.split(":", 1)[1] for r in labels if r.startswith("dialogue.speaker:")})
        event["narrated"] = bool(prose)
        if 'plot_execution' in w.narrative:
            from ..plot_execution import finalize_narration
            event['referents'] = sorted(set(event['referents']) | {
                r.split(':',1)[1] for r in labels if r.startswith('scoped_referent:')})
            finalize_narration(w,event)
        if prose:
            if scenes:
                offset += 1
            scenes.append(dict(event_id=event["id"], frame=asdict(frame), text=prose,
                start=offset, end=offset + len(prose), claims=plans[frame].claims,
                speakers=event["speakers"], rules=labels))
            offset += len(prose)
        traces.append(dict(event_id=event["id"], frame=asdict(frame), narrated=bool(prose),
                           probability=probability, grammar_probability=expected,
                           grammar_derivations=len(forest.derivations),
                           grammar_surfaces=len({d.tokens for d in forest.derivations}),
                           word_trace=trace, event_evidence=forest.evidence))
        if predict_attributes:
            traces[-1]["attribute_table"] = forest.attribute_table
    if not w.finished:
        raise AssertionError(f"world did not finish within {event_limit} events")
    story = " ".join(s["text"] for s in scenes)
    result = dict(scenario=scenario, seed=seed, tense=tense, options=options, story=story,
        attention=attention, temperature=temperature, continuations=continuations,
        symbolic_heads=heads.metadata() if heads else None,
        text_sha256=hashlib.sha256(story.encode()).hexdigest(), scenes=scenes,
        initial_world=initial, final_world=w.to_dict(), trace=traces)
    if predict_attributes:
        result["attribute_generation"] = dict(schema="joint-annotated-tokens-v1",
            conditioning="surface_word", periods=list(rotary.periods), tokens=attribute_stream)
    if annotations is not None:
        annotations_namespace = f"{scenario}:{seed}:{result['text_sha256']}"
        result["token_annotations"] = annotations.finish(annotations_namespace)
    from .seed_worlds.catalog import SEED_SCENARIOS, source_record
    if scenario in SEED_SCENARIOS:
        result['source_story'] = source_record(scenario)
    if presentation:
        from ..story_presentation import add_presentation
        result = add_presentation(result)
    return result


def replay(row):
    pack, w = setup(row["scenario"], row["seed"], **row.get("options", {}))
    assert w.to_dict() == row["initial_world"]
    for saved in row["final_world"]["history"][len(row["initial_world"]["history"]):]:
        f = Frame(**{**saved["frame"], "cause_ids": tuple(saved["frame"]["cause_ids"])})
        assert w.snapshot() == saved["before"]
        decision=None
        if 'beats' in w.narrative:
            from ..beat_generation import select,commit as commit_beats
            labels=['beat.selection:'+saved['beat_decision']['selected']] if saved.get('beat_decision') else []
            decision=select(pack,w,f,labels,row['tense'])
            assert decision==saved.get('beat_decision')
        record = pack.commit(w, f, saved["sentence"])
        if 'beats' in w.narrative:commit_beats(pack,w,record,decision)
        for key in ("referents", "speakers", "narrated"):
            record[key] = saved[key]
        if 'plot_execution' in w.narrative:
            from ..plot_execution import finalize_narration
            finalize_narration(w,record)
        assert w.snapshot() == saved["after"]
    assert w.to_dict() == row["final_world"]
    return True
