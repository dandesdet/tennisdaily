(() => {
  const section = document.getElementById('coaches');
  if (section.hidden) return;

  const coaches = [
    {
      id: 'aziza', years: 7, rating: 4.9,
      name: ['Азиза Садыкова', 'Aziza Sodiqova', 'Aziza Sodikova'],
      teaser: ['Первые шаги на корте', 'Kortdagi ilk qadamlar', 'First steps on court'],
      level: ['Начинающие · взрослые и дети от 8 лет', 'Boshlovchilar · kattalar va 8 yoshdan bolalar', 'Beginners · adults and children ages 8+'],
      bio: ['Учит держать мяч в игре и уверенно начинать розыгрыш. Подходит для первой тренировки.', 'To‘pni o‘yinda ushlab turish va ochkoni ishonch bilan boshlashni o‘rgatadi. Birinchi mashg‘ulot uchun mos.', 'Learn to rally and start a point with confidence. A good fit for your first lesson.'],
      review: ['Уже на первом занятии получилось несколько раз подряд перебить мяч через сетку.', 'Birinchi mashg‘ulotdayoq to‘pni to‘r ustidan bir necha marta ketma-ket oshira oldim.', 'In my first lesson I managed to hit the ball over the net several times in a row.'],
      times: [['09:00', '11:00'], ['10:00', '17:00'], ['09:00', '12:00']],
    },
    {
      id: 'timur', years: 9, rating: 4.8,
      name: ['Тимур Каримов', 'Timur Karimov', 'Timur Karimov'],
      teaser: ['Подача и тактика в паре', 'To‘p uzatish va juftlik taktikasi', 'Serve and doubles tactics'],
      level: ['Средний уровень · взрослые', 'O‘rta daraja · kattalar', 'Intermediate · adults'],
      bio: ['Работает над подачей, приёмом и тактикой в паре. На тренировке разбирает игровые ситуации.', 'To‘p uzatish, qabul qilish va juftlik taktikasini mashq qildiradi. O‘yin vaziyatlarini tahlil qiladi.', 'Work on serve, return and doubles tactics through match situations.'],
      review: ['Понял, куда смещаться после подачи партнёра. В паре стало легче читать игру.', 'Sherigim to‘p uzatgandan keyin qayerga siljishni tushundim. Juftlikda o‘yinni o‘qish osonlashdi.', 'I learned where to move after my partner serves. Doubles points became easier to read.'],
      times: [['12:00', '18:00'], ['16:00', '19:00'], ['11:00', '18:00']],
    },
    {
      id: 'dilnoza', years: 12, rating: 5,
      name: ['Дильноза Рахимова', 'Dilnoza Rahimova', 'Dilnoza Rahimova'],
      teaser: ['Подготовка к турнирам', 'Turnirlarga tayyorgarlik', 'Tournament preparation'],
      level: ['Продвинутый уровень · юниоры и взрослые', 'Yuqori daraja · o‘smirlar va kattalar', 'Advanced · juniors and adults'],
      bio: ['Готовит к турнирам. Работает над перемещением, выбором удара и планом на матч.', 'Turnirlarga tayyorlaydi. Kortda harakatlanish, zarba tanlash va o‘yin rejasini mashq qildiradi.', 'Prepare for tournaments with footwork, shot selection and match planning.'],
      review: ['Вышел на турнир с понятным планом на матч и знал, что менять по ходу игры.', 'Turnirga aniq reja bilan chiqdim va o‘yin davomida nimani o‘zgartirishni bildim.', 'I went into the tournament with a clear match plan and knew what to adjust mid-match.'],
      times: [['08:00', '16:00'], ['09:00', '18:00'], ['10:00', '15:00']],
    },
  ];
  const languages = ['ru', 'uz', 'en'];
  const localized = values => values.map((value, i) => `<span data-${languages[i]}>${value}</span>`).join('');
  const dateFormats = languages.map(lang => new Intl.DateTimeFormat(lang, {
    timeZone: 'Asia/Tashkent', weekday: 'short', day: 'numeric', month: 'short',
  }));
  const today = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Tashkent', year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(new Date());
  const datePart = type => Number(today.find(part => part.type === type).value);
  const dates = [1, 2, 3].map(offset => new Date(Date.UTC(datePart('year'), datePart('month') - 1, datePart('day') + offset)));
  const dateLabel = date => localized(dateFormats.map(format => format.format(date)));
  const bookedLabel = localized(['Занято', 'Band', 'Booked']);
  const photo = coach => `img/coaches/${coach.id}.webp`;
  const meta = ({years, rating}) => `<div class="coach-meta">
    <span class="coach-rating"><span aria-hidden="true">★</span> ${localized(languages.map(lang => new Intl.NumberFormat(lang, {minimumFractionDigits:1}).format(rating) + ' / 5'))}</span>
    <span>${localized([`${years} лет стажа`, `${years} yil tajriba`, `${years} years coaching`])}</span>
  </div>`;
  const grid = section.querySelector('.coach-grid');
  const dialog = document.getElementById('coach-dialog');
  const title = dialog.querySelector('h2');
  const detail = dialog.querySelector('.coach-detail');
  const selection = dialog.querySelector('.coach-selection');
  const form = dialog.querySelector('.coach-form');
  const bookings = new Set();
  let opener, selectedButton;

  grid.innerHTML = coaches.map(coach => `
    <article class="coach-card">
      <img src="${photo(coach)}" alt="" width="960" height="720" loading="lazy" decoding="async">
      <div class="coach-card-copy">
        <h3><button type="button" class="coach-open" data-coach="${coach.id}" aria-haspopup="dialog" aria-controls="coach-dialog">${localized(coach.name)}</button></h3>
        <p>${localized(coach.teaser)}</p>
        ${meta(coach)}
      </div>
    </article>
  `).join('');

  const showSchedule = () => {
    form.hidden = true;
    form.reset();
    detail.hidden = false;
  };

  function renderProfile(coach) {
    detail.innerHTML = `
    <img src="${photo(coach)}" alt="" width="960" height="720">
    <div class="coach-detail-copy">
      ${meta(coach)}
      <p class="coach-level">${localized(coach.level)}</p>
      <p>${localized(coach.bio)}</p>
      <div class="coach-days">
        <h4>${localized(['Расписание', 'Jadval', 'Schedule'])}</h4>
        <p class="coach-timezone">${localized(['Время Ташкента · 60 мин', 'Toshkent vaqti · 60 daqiqa', 'Tashkent time · 60 min'])}</p>
        ${dates.map((date, day) => `
          <div class="coach-day">
            <time datetime="${date.toISOString().slice(0, 10)}">${dateLabel(date)}</time>
            <div class="coach-slots">
              ${coach.times[day].map((time, index) => {
                const key = `${coach.id}/${date.toISOString().slice(0, 10)}/${time}`;
                const booked = bookings.has(key) || (day === 1 && index === 0);
                return `<button type="button" class="coach-slot" data-slot="${key}" data-time="${time}"${booked ? ' disabled' : ''}>${time}${booked ? ` <span class="post-share-label">${bookedLabel}</span>` : ''}</button>`;
              }).join('')}
            </div>
          </div>
        `).join('')}
        <p class="coach-status" role="status" tabindex="-1"></p>
      </div>
      <blockquote><p class="coach-timezone">${localized(['Пример отзыва', 'Fikr namunasi', 'Sample review'])}</p><p>${localized(coach.review)}</p></blockquote>
    </div>`;
  }

  grid.addEventListener('click', event => {
    const button = event.target.closest('.coach-open');
    if (!button) return;
    opener = button;
    const coach = coaches.find(item => item.id === button.dataset.coach);
    title.innerHTML = localized(coach.name);
    renderProfile(coach);
    showSchedule();
    dialog.showModal();
    title.focus();
  });

  detail.addEventListener('click', event => {
    const button = event.target.closest('.coach-slot');
    if (!button || button.disabled) return;
    selectedButton = button;
    const date = button.closest('.coach-day').querySelector('time');
    selection.innerHTML = `${date.outerHTML} · ${button.dataset.time}`;
    detail.hidden = true;
    form.hidden = false;
    form.querySelector('input').focus();
  });

  form.querySelector('.coach-back').addEventListener('click', () => {
    showSchedule();
    selectedButton.focus();
    selectedButton = undefined;
  });

  form.addEventListener('submit', event => {
    event.preventDefault();
    if (!selectedButton) return;
    bookings.add(selectedButton.dataset.slot);
    selectedButton.disabled = true;
    selectedButton.insertAdjacentHTML('beforeend', ` <span class="post-share-label">${bookedLabel}</span>`);
    const status = detail.querySelector('.coach-status');
    showSchedule();
    status.innerHTML = localized([
      'Пробная запись оформлена. Слот отмечен как занятый на этой странице.',
      'Sinov yozuvi yakunlandi. Slot shu sahifada band deb belgilandi.',
      'Demo booking complete. The slot is marked booked on this page.',
    ]);
    status.focus();
    selectedButton = undefined;
  });

  dialog.addEventListener('close', () => {
    showSchedule();
    opener?.focus({preventScroll: true});
    opener = undefined;
    selectedButton = undefined;
  });
})();
