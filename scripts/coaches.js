(() => {
  const section = document.getElementById('coaches');
  if (section.hidden) return;

  const coaches = [
    {
      id: 'aziza', initials: 'AS',
      name: ['Азиза Садыкова', 'Aziza Sodiqova', 'Aziza Sodikova'],
      level: ['Начинающие · взрослые и дети от 8 лет', 'Boshlovchilar · kattalar va 8 yoshdan bolalar', 'Beginners · adults and children ages 8+'],
      bio: ['Учит держать мяч в игре и уверенно начинать розыгрыш. Подходит для первой тренировки.', 'To‘pni o‘yinda ushlab turish va ochkoni ishonch bilan boshlashni o‘rgatadi. Birinchi mashg‘ulot uchun mos.', 'Learn to rally and start a point with confidence. A good fit for your first lesson.'],
      times: [['09:00', '11:00'], ['10:00', '17:00'], ['09:00', '12:00']],
    },
    {
      id: 'timur', initials: 'TK',
      name: ['Тимур Каримов', 'Timur Karimov', 'Timur Karimov'],
      level: ['Средний уровень · взрослые', 'O‘rta daraja · kattalar', 'Intermediate · adults'],
      bio: ['Работает над подачей, приёмом и тактикой в паре. На тренировке разбирает игровые ситуации.', 'To‘p uzatish, qabul qilish va juftlik taktikasini mashq qildiradi. O‘yin vaziyatlarini tahlil qiladi.', 'Work on serve, return and doubles tactics through match situations.'],
      times: [['12:00', '18:00'], ['16:00', '19:00'], ['11:00', '18:00']],
    },
    {
      id: 'dilnoza', initials: 'DR',
      name: ['Дильноза Рахимова', 'Dilnoza Rahimova', 'Dilnoza Rahimova'],
      level: ['Продвинутый уровень · юниоры и взрослые', 'Yuqori daraja · o‘smirlar va kattalar', 'Advanced · juniors and adults'],
      bio: ['Готовит к турнирам. Работает над перемещением, выбором удара и планом на матч.', 'Turnirlarga tayyorlaydi. Kortda harakatlanish, zarba tanlash va o‘yin rejasini mashq qildiradi.', 'Prepare for tournaments with footwork, shot selection and match planning.'],
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
  const grid = section.querySelector('.coach-grid');
  const dialog = document.getElementById('coach-dialog');
  const title = dialog.querySelector('h2');
  const selection = dialog.querySelector('.coach-selection');
  const form = dialog.querySelector('.coach-form');
  let selectedButton;

  grid.innerHTML = coaches.map(coach => `
    <article class="coach-card" data-coach="${coach.id}">
      <div class="coach-profile">
        <span class="coach-initials" aria-hidden="true">${coach.initials}</span>
        <div>
          <h3 tabindex="-1">${localized(coach.name)}</h3>
          <p class="coach-level">${localized(coach.level)}</p>
        </div>
      </div>
      <p>${localized(coach.bio)}</p>
      <div class="coach-days">
        <h4>${localized(['Расписание', 'Jadval', 'Schedule'])}</h4>
        <p class="coach-timezone">${localized(['Время Ташкента · 60 мин', 'Toshkent vaqti · 60 daqiqa', 'Tashkent time · 60 min'])}</p>
        ${dates.map((date, day) => `
          <div class="coach-day">
            <time datetime="${date.toISOString().slice(0, 10)}">${dateLabel(date)}</time>
            <div class="coach-slots">
              ${coach.times[day].map((time, index) => {
                const booked = day === 1 && index === 0;
                return `<button type="button" class="coach-slot" data-time="${time}" ${booked ? 'disabled' : 'aria-haspopup="dialog" aria-controls="coach-dialog"'}>${time}${booked ? ` <span class="post-share-label">${bookedLabel}</span>` : ''}</button>`;
              }).join('')}
            </div>
          </div>
        `).join('')}
        <p class="coach-status" role="status"></p>
      </div>
    </article>
  `).join('');

  grid.addEventListener('click', event => {
    const button = event.target.closest('.coach-slot');
    if (!button || button.disabled) return;
    selectedButton = button;
    const card = button.closest('.coach-card');
    card.querySelector('.coach-status').textContent = '';
    title.innerHTML = card.querySelector('h3').innerHTML;
    const date = button.closest('.coach-day').querySelector('time');
    selection.innerHTML = `${date.outerHTML} · ${button.dataset.time}`;
    dialog.showModal();
    form.querySelector('input').focus();
  });

  form.addEventListener('submit', event => {
    event.preventDefault();
    selectedButton.disabled = true;
    selectedButton.removeAttribute('aria-haspopup');
    selectedButton.removeAttribute('aria-controls');
    selectedButton.insertAdjacentHTML('beforeend', ` <span class="post-share-label">${bookedLabel}</span>`);
    selectedButton.closest('.coach-card').querySelector('.coach-status').innerHTML = localized([
      'Пробная запись оформлена. Слот отмечен как занятый на этой странице.',
      'Sinov yozuvi yakunlandi. Slot shu sahifada band deb belgilandi.',
      'Demo booking complete. The slot is marked booked on this page.',
    ]);
    dialog.close();
  });

  dialog.addEventListener('close', () => {
    form.reset();
    if (selectedButton.disabled) selectedButton.closest('.coach-card').querySelector('h3').focus({preventScroll: true});
    else selectedButton.focus({preventScroll: true});
    selectedButton = undefined;
  });
})();
