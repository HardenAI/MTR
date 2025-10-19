# Synapse MTR - Help Guide

This guide will help you use Synapse MTR to understand the source of network problems like lag, high ping, or disconnections.

## English

### How to Read the Results

The table shows the path your internet traffic takes to the game server. Each numbered "hop" is a router along the way.

- **Hop #**: The step number in the path. Hop 1 is usually your home router.
- **Hostname**: The address of the router for that hop.
- **Loss %**: The percentage of data packets that are lost at this hop. **This is the most important number.** Any consistent loss (above 0-1%) is a problem.
- **Avg**: The average time (in milliseconds) it takes for data to reach this hop and return. This is your "ping" to that router.
- **Jitter**: The variation in your ping time. High jitter means an unstable connection, which can feel like lag spikes.
- **Stability**: A summary of the connection quality at that hop based on loss, latency, and jitter. "Excellent" or "Good" is what you want to see.

### How to Diagnose the Problem

Look for the **first hop** in the list where `Loss %` consistently rises or where the `Avg` ping jumps up significantly and **stays high for all the hops after it**.

#### Scenario 1: The problem is on your PC or Local Network

- **What to look for in the app**: High `Loss %` or `Avg` ping on the **first 1 or 2 hops**.
- **Meaning**: The problem is happening before your data even leaves your home.
- **What to do**:
    1. Restart your PC.
    2. Restart your router.
    3. If using Wi-Fi, try connecting with an Ethernet cable.

#### Scenario 2: The problem is with your Internet Service Provider (ISP)

- **What to look for in the app**: The first few hops are fine (green), but high `Loss %` or `Avg` ping starts at a hop in the middle of the list (e.g., hop 3-7) and continues all the way to the end.
- **Meaning**: Your ISP's network is having trouble routing your traffic.
- **What to do**:
    1. Use the "Export to HTML" button to save a report.
    2. Contact your ISP's support.
    3. Tell them you are experiencing packet loss or high latency starting at a specific hop and provide them with the report.

#### Scenario 3: The problem is with the Game Server

- **What to look for in the app**: The connection is stable (all green) for most of the path, but the `Loss %` or `Avg` ping suddenly gets very high on the **last few hops**.
- **Meaning**: Your connection to the game server's own network is the issue. Your ISP cannot fix this.
- **What to do**:
    1. Check the game's official website, Twitter, or forums for any server status announcements.
    2. Report the issue to the game's support team, possibly attaching the MTR report.

**Important Note:** Sometimes a single hop in the middle will show high loss, but the hops after it are fine. This is usually because that specific router is busy and configured to ignore ping requests. If the loss **does not continue** to the final destination, you can safely ignore it.

---

## Türkçe

### Sonuçlar Nasıl Okunur?

Tablo, internet trafiğinizin oyun sunucusuna ulaşmak için izlediği yolu gösterir. Numaralandırılmış her "hop" (atlama), yol üzerindeki bir yönlendiricidir (router).

- **Hop #**: Güzergahtaki adım numarası. 1. hop genellikle evinizdeki modem/router'dır.
- **Hostname**: O adımdaki yönlendiricinin adresi.
- **Loss %**: Veri paketlerinin bu adımda kaybolma yüzdesi. **Bu en önemli metriktir.** Sürekli devam eden herhangi bir kayıp (%0-1 üzeri) bir soruna işaret eder.
- **Avg**: Verinin bu yönlendiriciye ulaşıp geri dönmesinin ne kadar sürdüğünün ortalaması (milisaniye cinsinden). Bu, o yönlendiriciye olan "ping" sürenizdir.
- **Jitter**: Ping sürenizdeki değişkenlik. Yüksek jitter, ani takılmalar (lag spike) olarak hissedilen istikrarsız bir bağlantı anlamına gelir.
- **Stability**: Paket kaybı, gecikme ve jitter değerlerine dayalı olarak o adımdaki bağlantı kalitesinin bir özetidir. "Excellent" (Mükemmel) veya "Good" (İyi) görmek istersiniz.

### Sorun Nasıl Teşhis Edilir?

Listede `Loss %` değerinin sürekli olarak artmaya başladığı veya `Avg` ping süresinin önemli ölçüde yükselip **ondan sonraki tüm adımlarda yüksek kaldığı ilk hop'u (adımı) bulun**.

#### Senaryo 1: Sorun bilgisayarınızda veya yerel ağınızda

- **Uygulamada ne görmelisiniz**: **İlk 1-2 hop'ta** yüksek `Loss %` veya `Avg` ping değeri.
- **Anlamı**: Sorun, veriniz daha evinizden çıkmadan yaşanıyor.
- **Ne yapmalısınız**:
    1. Bilgisayarınızı yeniden başlatın.
    2. Modeminizi/router'ınızı yeniden başlatın.
    3. Wi-Fi kullanıyorsanız, Ethernet kablosu ile bağlanmayı deneyin.

#### Senaryo 2: Sorun İnternet Servis Sağlayıcınızda (İSS)

- **Uygulamada ne görmelisiniz**: İlk birkaç hop normal (yeşil), ancak listenin ortalarındaki bir hop'ta (örneğin 3-7. adımlar) yüksek `Loss %` veya `Avg` ping başlıyor ve sonuna kadar devam ediyor.
- **Anlamı**: İSS'nizin ağında trafiğinizi yönlendirirken bir sorun yaşanıyor.
- **Ne yapmalısınız**:
    1. "Export to HTML" butonu ile bir rapor kaydedin.
    2. İSS'nizin müşteri hizmetleriyle iletişime geçin.
    3. Onlara belirli bir hop'tan itibaren paket kaybı veya yüksek gecikme yaşadığınızı söyleyin ve kaydettiğiniz raporu iletin.

#### Senaryo 3: Sorun Oyun Sunucusunda

- **Uygulamada ne görmelisiniz**: Bağlantı yolun büyük bir kısmında stabil (tamamı yeşil), ancak `Loss %` veya `Avg` ping **son birkaç hop'ta** aniden çok yükseliyor.
- **Anlamı**: Sorun, oyun sunucusunun kendi ağındadır. Sizin veya İSS'nizin yapabileceği bir şey yoktur.
- **Ne yapmalısınız**:
    1. Oyunun resmi web sitesini, Twitter hesabını veya forumlarını kontrol ederek sunucu durumu hakkında bir duyuru olup olmadığına bakın.
    2. Sorunu, mümkünse MTR raporunu ekleyerek oyunun destek ekibine bildirin.

**Önemli Not:** Bazen ortadaki tek bir hop yüksek kayıp gösterebilir, ancak ondan sonrakiler normaldir. Bu genellikle o yönlendiricinin meşgul olduğu ve ping isteklerini önceliklendirmediği anlamına gelir. Eğer kayıp, son hedefe kadar **devam etmiyorsa**, bu durumu genellikle görmezden gelebilirsiniz.
