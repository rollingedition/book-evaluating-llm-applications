---
chapter_id: intervals-and-sample-size
---

# Decide whether a change is better, and how many questions you need

By the end of this chapter you can say whether a difference between two versions of the assistant is more than noise, using an interval on a paired comparison. You can also work out how many questions a difference of a given size needs before a test can show it.

[Chapter 1](measure-before-you-change) measured the assistant once and gave its pass rate an interval. It then compared two prompts on twenty items. The interval on their difference was {{out:twenty-cannot-tell:interval width}} wide, and the chapter ended on a promise: a later chapter would work out how many items a difference needs before it can show. This chapter keeps that promise. A team that changes a prompt needs three answers. Did the rate move for a reason beyond the chance in the test? Was the comparison able to show a difference at all? And how many questions would it need to show the difference it cares about?

Every number here comes from one assistant model, Qwen3-4B-Instruct-2507, and one judge, the same model run at temperature zero. The intervals cover the spread that comes from drawing items. The first section measures the spread from sampling replies, without an interval. They don't cover the biases of the judge, which [Chapter 7](when-the-judge-stops-being-reliable) tests. Read each result with that in mind.

## Variance within one item {#variance-within-one-item}

Ask the same question twice and a model can answer differently. This chapter's comparisons use one recorded reply per item and prompt, so each verdict rests on one reply. At a higher temperature the model samples, and an item's verdict can change from one sample to the next. That matters for comparisons. A difference between two prompts that is smaller than the swing from one sample to the next isn't a difference at all, and a rate read from one run hides the swing.

The variance set holds five samples of the assistant's reply to each dev item, drawn at temperature 0.7. The judge reads every reply at temperature zero. An item flips when its five verdicts are not all the same. Counting the flips gives a measure of how much the verdicts move from sample to sample, before any change is made.

[Example: flip-rate](../examples/flip-rate.py)

Counting per item, the code tallies how many of its five samples the judge passed. An item with a verdict that can't be read is left out, not counted as a fail, and the output names the item it left out.

Most items don't move. {{out:flip-rate:items with 5 of 5 PASS}} items pass all five samples, and {{out:flip-rate:items with 0 of 5 PASS}} fail all five. Of the items that flip, {{out:flip-rate:items with 1 of 5 PASS}} passes one sample and {{out:flip-rate:items with 4 of 5 PASS}} passes four.

The flip rate is {{out:flip-rate:flip rate}}.

The mean pass rate across all the samples is {{out:flip-rate:mean per-item pass rate across samples}}. The baseline, one reply per item at temperature zero, passes {{out:flip-rate:baseline pass rate, same items (temperature 0)}}. The two are equal, and the two flipping items pull in opposite directions. That holds for P1, the prompt the variance set uses, and another prompt might be less steady.

That is a narrow result. A set with more borderline questions would flip more, and the flip rate counts items and has no interval of its own. A count of flipping items this small says little about how often the next change will flip.

The flip rate measures only the spread that comes from sampling this assistant's replies, with the items held fixed. A comparison between two prompts also moves with the items each prompt gets right. The last section uses that sampling spread as a lower bound, and only for a comparison that samples its replies: [How many questions a difference needs](#how-many-questions).

**Working rule:** Before you trust one run's rate, run the variance set at the temperature you ship, and read the flip rate beside the mean pass rate. The flip rate says how far sampling moves one prompt's verdicts. It bounds a comparison only when that comparison samples its replies too.

## The bootstrap over items {#bootstrap-over-items}

[Chapter 1](measure-before-you-change#a-pass-rate-and-its-interval) showed an interval on a pass rate and used it to read a small set. This section explains the method, because the rest of the chapter uses it three ways: on a rate, on a paired difference, and on a difference that has to clear a stricter level.

The method is the [percentile bootstrap](#a-pass-rate-and-its-interval). The items in a set are one sample of the questions a team could have written, so a different set would give a somewhat different rate. To estimate how much, draw items from the set with replacement, as many as the set holds, so that some items come up twice and some not at all. Compute the statistic for that draw, repeat the draw many times, and keep the middle 95% of the results. The bootstrap adds no data. It reuses the items the set already has, and it shows how far the statistic would move if the set had been another draw of the same kind.

The unit of resampling is the item, and that is the rule to keep. For a rate, each item contributes its verdict. For a paired difference, each item contributes one number: the verdict of prompt B minus the verdict of the baseline, which is plus one, zero or minus one. For the variance set, the five samples of an item are kept together, because they answer one question. Drawing them apart would make them look like five independent questions, and the interval would come out too narrow. [Miller (2024)](https://arxiv.org/abs/2411.00640) makes the same point for questions that come in related groups. That paper is a preprint and a practitioner's note, not a reviewed method, so this book uses it for the reason and not as proof.

The book fixes the settings so that a number can be reproduced. The method draws 2,000 resamples with a seed of zero, and it creates a fresh random generator inside each call. The same data therefore gives the same interval, whatever ran before it. The seed is a choice, not a property of the data. A different seed moves the endpoints a little, which is why the settings are written down.

The method also depends on the set being a fair sample of the questions, which [Chapter 1](measure-before-you-change) argued and no interval can check. A small set gives a rough interval. The endpoints of a percentile interval on a set of this size are a first estimate, and they should be read as approximate.

**Working rule:** Resample items, never runs within an item, and keep an item's samples together. Fix the resample count and the seed in the code, so the same data gives the same interval. When the set holds few items, call the interval rough and say so beside it.

## Paired comparisons {#paired-comparisons}

Two prompts answer the same questions, so their results are paired. A paired comparison subtracts, for each item, the verdict of the baseline from the verdict of the variant, here prompt B, and averages the differences over the set. Its interval comes from the bootstrap over items.

Pairing matters because most items agree. An item that both prompts pass, or both fail, contributes nothing to the difference, whatever the question's difficulty. The comparison's spread comes from the items on which the two prompts split. An unpaired comparison takes two separate pass rates and sets them side by side. It carries the variation between questions on every item, including the ones that agree, and that variation can hide a real difference. The paired version cancels the part the two prompts share. The argument for paired differences in Miller (2024) says the same: the variance of a paired difference falls as long as the two models' scores on each item are positively correlated.

[Example: paired-prompt-b](../examples/paired-prompt-b.py)

Here prompt B runs against the baseline on the dev items. An item with a verdict that can't be read under either prompt is left out of both sides, because a paired difference needs the same items on both sides. The printed lines give each pass rate, the difference, its interval and the number of paired items.

The baseline passes {{out:paired-prompt-b:P1 (baseline) pass rate}}. Prompt B passes {{out:paired-prompt-b:P2 (prompt-b) pass rate}}. The difference, prompt B minus the baseline, is {{out:paired-prompt-b:difference, P2 minus P1}}, with a 95% interval of {{out:paired-prompt-b:95% interval of the difference}}.

The split shows where the difference lives. {{out:paired-prompt-b:items both pass}} items pass under both prompts, and {{out:paired-prompt-b:items neither passes}} fail under both. Only the items that split move the difference: {{out:paired-prompt-b:items only P2 passes}} pass only under prompt B, and {{out:paired-prompt-b:items only P1 passes}} pass only under the baseline.

The interval includes zero, so the reading is {{out:paired-prompt-b:reading}}. The interval runs from a drop to a rise, and this set can't say which end is nearer. No difference detected, the reading when the interval includes zero, is a finding about a set at its size. It is not a claim that the prompts are equal, and the text shouldn't say they are.

**Working rule:** Compare variants on the same items, paired, and report the difference with its interval and n. Call one variant better only when the whole interval sits above zero, and worse only when the whole interval sits below it. When the interval includes zero, report no difference detected at that n, and say how many items the difference would need, as [How many questions a difference needs](#how-many-questions) works out.

## Held-out, once {#held-out-once}

Dev items are for building. A team may tune a prompt on them, read the failures and change the next version. The dev results can't then prove that a change works, because the change was shaped by them. The [held-out set](#dev-and-held-out) is the check that isn't tuned. A comparison on held-out is run once, against rules fixed before the run: the variants, the level and the reading. Run it again after a change of mind, or choose the level after seeing the number, and the interval no longer means what it says.

This section runs three comparisons on the held-out set, each variant against the baseline. Prompt B is the one from [Paired comparisons](#paired-comparisons). The variant k5 retrieves five sections instead of three. The variant unfiltered retrieves from every version of the docs at once, with three sections, instead of only the asked version.

[Example: held-out-variants](../examples/held-out-variants.py)

Three comparisons share one held-out set, so each interval is set at a higher level than 95%, and [Many comparisons](#many-comparisons) explains why. The level is {{out:held-out-variants:level of each interval, 1 - 0.05 / m}}. Each variant gets a difference, an interval, a count of paired items and a reading, all printed.

Held-out has {{out:sample-size-limits:held-out items (n)}} items, against {{out:paired-prompt-b:paired items (n)}} on dev. So its intervals are wider for the same difference, and a result on it can only be as sharp as its item count allows. The split keeps a result honest, and its cost is fewer items to spend.

The difference for prompt B is {{out:held-out-variants:prompt-b minus baseline, difference}}, with an interval of {{out:held-out-variants:prompt-b minus baseline, 98.33% interval}}. The comparison has {{out:held-out-variants:prompt-b minus baseline, n}} paired items.

The k5 difference is {{out:held-out-variants:k5 minus baseline, difference}}, with an interval of {{out:held-out-variants:k5 minus baseline, 98.33% interval}}. The unfiltered difference is {{out:held-out-variants:unfiltered minus baseline, difference}}, with an interval of {{out:held-out-variants:unfiltered minus baseline, 98.33% interval}}.

Dev gave {{out:paired-prompt-b:difference, P2 minus P1}} for the same prompt, and the two point estimates differ. The {{out:sample-size-limits:held-out items (n)}} held-out items can't tell which is nearer the truth. The smallest difference that they detect, at 98.33% confidence and 80% power, is {{out:sample-size-limits:smallest difference 40 held-out items detect at 98.33% and 80% power}}, so both point estimates sit below what this set can detect. [How many questions a difference needs](#how-many-questions) works out the arithmetic.

By the rule, all three read as no difference detected. For prompt B the printed reading is {{out:held-out-variants:prompt-b minus baseline, reading}}. For k5 it is {{out:held-out-variants:k5 minus baseline, reading}}, and for unfiltered {{out:held-out-variants:unfiltered minus baseline, reading}}.

Prompt B is the close case. Its interval is {{out:held-out-variants:prompt-b minus baseline, 98.33% interval}}, and its lower end is exactly zero. The reading rule says better only when the whole interval sits above zero, and this one reaches zero without clearing it, so by the rule the reading is no difference detected. Beyond each end of the interval lie {{out:held-out-variants:resamples beyond each end of an interval}} of the 2,000 resamples, so the call sits on the line. The seed was fixed before the run for that reason. A reader could argue that a point estimate of that size should count for something, and this section doesn't make that argument. The rule was set before the run, the comparison runs once, and nobody gets to look at these three again with a lower level or a different reading. If prompt B is to be tested further, it needs a fresh held-out set, sized by [How many questions a difference needs](#how-many-questions) and fixed before anyone sees its results, read on its own. Adding items to the {{out:sample-size-limits:held-out items (n)}} already read, and rereading the pool, would be a second look at a result already seen.

**Working rule:** Fix the variants, the level and the reading rule before you open the held-out set, and run each comparison once. An interval that reaches zero is no difference detected at that n. Don't rerun the comparison, lower the level or change the reading to get a different answer. Add held-out items only before they are scored.

## Many comparisons {#many-comparisons}

Each comparison is a chance to be fooled. A 95% interval on a comparison with no real difference still excludes zero by luck about one time in twenty. Run three such comparisons, report each at 95%, and the chance that at least one of them reads as a difference rises above five in a hundred. The more comparisons a chapter reports, the more likely one of them is a lucky result.

The usual fix is the Bonferroni correction, which shares the error budget between the comparisons. With m comparisons of one metric, each interval is set at 1 minus 0.05 divided by m. For three comparisons, 0.05 divided by 3 is {{out:held-out-variants:share of the 5% for each comparison, 0.05 / m}}, so each interval's level is {{out:held-out-variants:level of each interval, 1 - 0.05 / m}}, the level the [held-out section](#held-out-once) used. The 0.05 is split between the two tails of each interval, so each tail gets 0.05 divided by twice m. The arithmetic holds whatever the comparisons have in common. The chance that any of them shows a false difference can't exceed the sum of their separate chances, and that sum is 5%.

The code computes the level from m and prints it, so a reader can check it against the count. The price is width. At this level each interval is wider than a 95% one, so a difference has to be larger before its interval clears zero. The sum of the separate chances is an upper bound on the chance of any false difference, so the correction is conservative whenever the comparisons' false results overlap. This book uses this one because its rule is short to state and to check, and a reader can recompute it from the count.

Which comparisons form the count? In this chapter, the dev comparison in the paired section stands alone, and it is reported at 95% because it is a worked example on tuning data. The three held-out comparisons form a family, and they are reported at the adjusted level. A reader who sees both should not read the dev interval as a held-out result, and the held-out result is the one the chapter relies on.

The count is part of the design. Count the comparisons of one metric that the chapter will report before you run any of them. A comparison added after the results is reported apart from the family, as exploratory, with its own count. The family's intervals stay as they were run, because setting them again after the results would change the rule the run was held to.

**Working rule:** Count the comparisons of one metric before you run them, and set each interval's level at 1 minus 0.05 divided by that count. Show the level beside every interval. A comparison added after the results is reported apart as exploratory, and the family's intervals are not set again.

## How many questions a difference needs {#how-many-questions}

The question to ask before a comparison is how many items it needs to show a difference of the size the team cares about. The answer depends on one quantity: how much the two variants disagree, item by item. Two prompts that disagree on few items show a small difference with few items.
The paired formula makes this concrete. Write z-conf for the two-sided normal value at the confidence level and z-power for the one at the power. Then n = (z-conf + z-power)² · var(d) / δ², where var(d) is the variance of one item's paired difference and δ is the difference to detect. The variance is the share of items on which the two variants disagree, minus the square of their average difference. So the estimate is driven by disagreement, not by the pass rates themselves. This section uses 95% confidence and 80% power.

[Example: sample-size](../examples/sample-size.py)

Here the code reads the disagreement between prompt B and the baseline on the dev items. Its assumption is printed, and it is the one to check: the next change disagrees with the baseline on about as many items as prompt B did. Here the share of items that disagree is {{out:sample-size:share of discordant items, P2 and P1 disagree}}.

[Example: sample-size-limits](../examples/sample-size-limits.py)

The worked arithmetic for a five-point difference runs in that example. The square of the sum of the two z values is {{out:sample-size-limits:z sum squared, 95% confidence and 80% power}}. The variance of one item's paired difference is {{out:sample-size-limits:var(d), variance of one item paired difference}}. The five-point difference squared is {{out:sample-size-limits:delta squared, a five-point difference}}. So n is {{out:sample-size-limits:n for five points}}.

Miller (2024) gives the paired formula in a more general form, with terms for the noise within each item. The formula here is that form with one reply per item, which drops the within-item terms. Its worked example, with the paper's inputs, comes to about 969 items. Those inputs describe a different experiment, so the book's own numbers come from the printed run only.

Power works the other way too. At 80% power, a set sized for a real difference still misses it about one time in five. That is the price of a fixed budget of questions, and a team that can't pay it should either accept a larger difference as its goal or enlarge the set before the run.

Because the items needed scale with that share when the average difference is small, a change that disagrees on twice as many items needs about twice the questions. A team should estimate the share from a paired run on dev, state it, and check it again when the change is bigger than the one it was measured on.

The main estimate says that a five-point difference needs {{out:sample-size:main estimate, items needed for a 5-point difference}} items, and a ten-point difference needs {{out:sample-size:main estimate, items needed for a 10-point difference}}. The floor uses only the sampling noise within each item, and it says {{out:sample-size:floor, sampling noise only, items needed for a 5-point difference}} and {{out:sample-size:floor, sampling noise only, items needed for a 10-point difference}}. Read the floor as a lower bound on what is needed, not as a plan. It leaves out the disagreement between variants, which is real. Two prompts change what the assistant says, not only how steadily it says it. The floor holds only for a comparison that samples one reply per item at temperature 0.7, with variants as steady as P1. Only two of the items add to its noise, so it rests on very few items. A plan made on the floor comes up short whenever a change disagrees more than sampling alone would explain.

The same estimate answers the question for Chapter 1's set. With twenty items, the smallest difference that the test detects with 80% power at 95% confidence is {{out:sample-size:main estimate, smallest difference that 20 items detect, 80% power and 95% confidence}}, under the disagreement assumed above.

Chapter 1's set disagreed on {{out:sample-size:chapter 1 set, share of items where the two verdicts differ}} of its items.

Its interval was {{out:sample-size:chapter 1 set, 95% interval width}} wide. The formula gives {{out:sample-size:main estimate, 95% width at 20 items}} at the same disagreement, which is close. The [twenty-item example](../examples/twenty-cannot-tell.py) shows that set. At that disagreement, twenty items would usually miss a difference of ten points, and a team that wants to see a difference of five points needs hundreds of items, not dozens.

The estimate rests on the discordant items alone, so it is an order of magnitude, not a count. Its 95% interval on the share is {{out:sample-size-limits:discordant share, 95% interval}}. Across that interval, a five-point difference needs {{out:sample-size-limits:items needed for 5 points, low end of the share}} items at the low end and {{out:sample-size-limits:items needed for 5 points, high end of the share}} at the high end. The formula is a normal approximation, while the reading rule uses a bootstrap, and the two agree only roughly when few items disagree. At the held-out level of 98.33%, the same inputs need {{out:sample-size-limits:items needed for 5 points at 98.33% confidence}} items for a five-point difference.

In production, the mistake is to pick a set size by feel and then read the result as a decision. A team that wants a five-point gain and runs a few dozen items will usually get no difference detected, and may take that for a verdict that the change doesn't work. Write the size down before the run, with the disagreement assumption, and report the result against it. No difference detected at a stated n is a finding about that set. It is not a failed change.

**Working rule:** Before a comparison, run a paired comparison on dev to estimate how often the two variants disagree, and state that share as the assumption. Compute the items needed for the difference you care about, at the level the comparison will be read at, and give its range from the interval on that share. If the set is smaller, report that it can't detect a difference that size, and don't read its no difference detected as a ruling against the change. Use the floor only as a lower bound, and only for a comparison that samples its replies.
