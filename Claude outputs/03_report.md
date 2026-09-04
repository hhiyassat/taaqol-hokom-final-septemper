# ذيلُ العمل — B17 · A4 · مقامُ G_IDENTICAL

```text
TASK_ID = TAIL_B17_A4_DENOM
HOKOM_HEAD = 30b389d3ad063d275300a0067e16321133d90ef8   (لم يتحرّك)
CLAIM_PROJECT_FINISHED = NO
```

## الحرّاس — بقيمها الحقيقيّة

| الحارس | القيمة | المقام / المصدر |
|---|---|---|
| `G_VENDOR` | `True` | `rev-parse` == PIN ∧ porcelain نظيف |
| `G_VENDOR_PINNED_IN_GIT` | `False` | `ls-tree HEAD` = `bc9d1ea5ef45` ≠ PIN `3cccdded7951` |
| `G_IDENTICAL` | `True` (2/2 مخرَجًا) | 20 ملفًّا في المرحلتين · 18 خارج المقابلة بأسبابها |
| `G_NO_COMMIT` | `True` | HEAD ثابت · ولا مؤشّرَ وحدةٍ التُزم |
| `NO_PROMOTION` | `True` | 5/5 قَطعًا مقيسًا · أوسام `0` |

## B17 — التثبيتُ في الشجرة لا في الالتزام

```text
committed_pointer  bc9d1ea5ef45970f5f3ec132441e30fd54b3da52
worktree_head      3cccdded7951ba71b3cb2a8b9b477f3fb3d91095
PIN                3cccdded7951ba71b3cb2a8b9b477f3fb3d91095
differ             True
```

مرفوعٌ إلى المالك ولم يُحسم. ولا مؤشّرَ التُزم، ولا `.gitmodules` مُسّ.

## A4 — حدُّ ما يراه الفحص

```text
أقدمُ قَطعٍ مقيس   2.8.0
أحدثُ قَطعٍ مقيس   2.12.0
مقبولٌ سلفًا عنده  كَبَائِرَ · كَتَبَ · كَفَرُوا · كِتَاْبُنْ
```

ما كان مقبولًا عند أقدم قَطعٍ مقيسٍ لا يُعرف متى رُقّي: الترقيةُ وقعت قبل حدّ الفحص. فـNO_PROMOTION تعني «لا ترقيةَ فيما قِيس»، لا «لم تقع ترقيةٌ قطّ».

## المقام

```text
PHASES_EMIT_ONLY_MANIFESTS = True
20 ملفًّا · دخل المقابلة 2 · خرج 18
```

* 12 — BYTECODE_CACHE — مولَّدٌ من المصدر، لا مخرَج
* 6 — SOURCE — هو المتغيّرُ نفسُه، لا المخرَج
