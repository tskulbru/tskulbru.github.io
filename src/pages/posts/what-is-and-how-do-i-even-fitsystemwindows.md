---
layout: ../../layouts/post.astro
title: "What is and how do I even fitSystemWindows?"
pubDate: 2020-03-23
description: "Understanding Android's fitSystemWindows property and how to properly handle system UI components like status bars and navigation bars in your Android applications."
author: "Torstein Skulbru"
isPinned: false
excerpt: "Since you are here, I'm guessing you've tumbled into the black abyss that is fitSystemWindows once or twice in the past. Learn what system windows are, why we want to fit them, and how to properly handle WindowInsets in Android development."
image:
  src: "/images/fitsystemwindows-hero.webp"
  alt: "Photo by Vidar Nordli-Mathisen on Unsplash, picture of a beatuiful lake view from inside a cabin"
tags: ["android", "ui", "system-windows", "mobile-development"]
modifiedDate: 2026-01-14
---

Since you are here, I'm guessing you've tumbled into the black abyss that is `fitSystemWindows` once or twice in the past. I know I have spent hours blindly adding `android:fitSystemWindows="true"` without understanding why my views _refused_ to adhere to this magical setting.

To understand this setting we first need to understand what system windows are, and why we want to _fit_ them. Basically system windows are system UI components, status bar and navigation bar (amongst others).

> System windows are the parts of the screen where the system is drawing either non-interactive (in the case of the status bar) or interactive (in the case of the navigation bar) content.
>
> Ian Lake — Why would I want to fitsSystemWindows?

Usually you don't want to draw or show some of your views underneath them. When you do however, you need to make sure that your _interactive elements_ (things that users click on, such as buttons) aren't partially or completely hidden underneath them.

## What does fitSystemWindows do?

OK, so what do you do then? Well that's exactly what `android:fitSystemWindows="true"` is for. What it does is it pads the view to ensure it doesn't collide with the system view, by utilizing something called WindowInsets. The WindowInsets changes on rotations and also knows about oddities such as the various display cutouts.

A typical example nowadays can be a `RecyclerView` where you want your content to scroll nicely underneath a transparent navigation bar. To do this properly, you would need to use `android:fitSystemWindows="true"` together with `android:clipToPadding="false"`. By applying that last one, your content looks beautiful while scrolling, and your last element will be properly padded to be shown above the navigation bar (thus, any user interaction won't be obstructed).

![fitsystemwindows=true all the things](/images/fitsystemwindows.webp)

## The Problems with fitSystemWindows

Cool right? So let's just always apply it whenever some system UI obstructs our controllers. Well I wish it was that easy (and to be fair, _sometimes_ it is). However, there's a few problems with how `fitSystemWindows` behaves.

- **It's applied depth first** — meaning the first View that consumes the inset, makes all the difference. Also, having it declared multiple times doesn't work, because it's already consumed by the first View.
- **Other padding is overwritten** — if you have any padding properties set on the same View that had `fitSystemWindows` set, you will notice that they are completely disregarded.
- **Some layout types react differently to the property** — some of the layouts behave as you most likely expected them to behave, while others don't really react at all. If however your containing view is `DrawerLayout / CoordinatorLayout / AppBarLayout` go ahead and use it and see if it solves your problem.

However more often than not, you need to use something else entirely. What if you have multiple independent views, both of which need to be fitted because your layout expands beneath the navbar and the status bar?

## setOnApplyWindowInsetsListener

If you have multiple views that require fitting, or if your view is inside the "wrong" parent layout, one excellent solution is to apply an `OnApplyWindowInsetsListener` to your views, and set your wanted insets/paddings.

```kotlin
val originalTopPadding = myView.paddingTop
ViewCompat.setOnApplyWindowInsetsListener(myView) { view, insets ->
    view.updatePadding(top = originalTopPadding + insets.systemWindowInsetTop)
    insets
}
```

One thing to note: WindowInsets can be dispatched both at any and multiple times during the view lifecycle. Because of this, we recorded the view's original top padding set by us (in our layout file for example), and added it to the system window inset. If we had simply looked it up inside our listener, it would've changed on each pass, causing it to increase each pass (probably not what you would've wanted).

## Continue Reading

I highly suggest you continue reading about both `fitSystemWindows` and `applyWindowInsetsListener`, because you can do so much with them (and it really depends on the situation you are in). I've rounded up some good articles and presentations you definitely should take a look at. I especially recommend **Windows Insets + Fragment Transitions** since it shows some more advanced use cases for the listener.

### Recommended Resources

- [Why would I want to fitsSystemWindows?](https://medium.com/androiddevelopers/why-would-i-want-to-fitsystemwindows-4e26d9ce1eec) by Ian Lake
- [WindowInsets — Listeners to layouts](https://medium.com/androiddevelopers/windowinsets-listeners-to-layouts-8f9ccc8fa4d1) - Moving where we handle insets to where our views live, layout files
- [Windows Insets + Fragment Transitions](https://medium.com/@chrisbanes/windows-insets-fragment-transitions-9024b239a436) - A tale of woe by Chris Banes
- [Becoming a master window fitter 🔧](https://chris.banes.dev/2019/04/12/insets-listeners/) - Window insets have long been a source of confusion to developers, and that's because they are indeed very confusing…

Understanding and properly implementing window insets handling is crucial for creating polished Android applications that work seamlessly across different devices and screen configurations. While `fitSystemWindows` can be a quick solution in some cases, mastering `OnApplyWindowInsetsListener` gives you the flexibility and control needed for complex UI scenarios.
