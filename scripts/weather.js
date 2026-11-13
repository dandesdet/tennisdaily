(() => {
  const forecast = document.querySelector('.weather');
  const days = forecast.querySelector('.weather-days');
  const scrollArea = forecast.querySelector('.weather-window');
  const status = forecast.querySelector('.weather-status');
  const languages = ['ru', 'uz', 'en'];
  const weekdays = languages.map(lang => new Intl.DateTimeFormat(lang, {weekday: 'short', timeZone: 'UTC'}));
  const conditions = [
    [[0], '☀️', ['Ясно', 'Ochiq', 'Clear']],
    [[1, 2], '⛅', ['Переменная облачность', 'Qisman bulutli', 'Partly cloudy']],
    [[3], '☁️', ['Облачно', 'Bulutli', 'Overcast']],
    [[45, 48], '🌫️', ['Туман', 'Tuman', 'Fog']],
    [[51, 53, 55, 56, 57], '🌦️', ['Морось', 'Mayda yomg‘ir', 'Drizzle']],
    [[61, 63, 65, 66, 67, 80, 81, 82], '🌧️', ['Дождь', 'Yomg‘ir', 'Rain']],
    [[71, 73, 75, 77, 85, 86], '❄️', ['Снег', 'Qor', 'Snow']],
    [[95, 96, 99], '⛈️', ['Гроза', 'Momaqaldiroq', 'Thunderstorm']],
  ];

  function appendTranslations(parent, values) {
    values.forEach((value, i) => {
      const span = document.createElement('span');
      span.dataset[languages[i]] = '';
      span.textContent = value;
      parent.append(span);
    });
  }

  function renderDay(date, index, daily) {
    const day = document.createElement('li');
    day.className = 'weather-day';
    const time = document.createElement('time');
    time.dateTime = date;
    if (index === 0) time.setAttribute('aria-current', 'date');
    appendTranslations(time, weekdays.map(format => format.format(new Date(date + 'T00:00:00Z'))));

    const [, symbol, description] = conditions.find(([codes]) => codes.includes(daily.weather_code[index])) ||
      [[], '–', ['Нет данных', 'Ma’lumot yo‘q', 'No data']];
    const icon = document.createElement('span');
    icon.className = 'weather-icon';
    icon.setAttribute('aria-hidden', 'true');
    icon.textContent = symbol;
    const label = document.createElement('span');
    label.className = 'post-share-label';
    appendTranslations(label, description);
    const reading = document.createElement('div');
    reading.className = 'weather-reading';
    const high = document.createElement('b');
    high.textContent = Math.round(daily.temperature_2m_max[index]) + '°';
    reading.append(time, high);
    day.append(icon, label, reading);
    return day;
  }

  const url = new URL('https://api.open-meteo.com/v1/forecast');
  url.search = new URLSearchParams({
    latitude: '41.3111',
    longitude: '69.2797',
    daily: 'weather_code,temperature_2m_max',
    timezone: 'Asia/Tashkent',
    forecast_days: '7',
  });
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 7000);
  fetch(url, {signal: controller.signal})
    .then(response => {
      if (!response.ok) throw new Error('Forecast request failed');
      return response.json();
    })
    .then(({daily}) => {
      if (!Array.isArray(daily?.time) || daily.time.length !== 7 ||
        daily.time.some((date, index) => typeof date !== 'string' ||
          !Number.isFinite(Date.parse(date + 'T00:00:00Z')) ||
          !Number.isFinite(daily.temperature_2m_max?.[index])) ||
        !Array.isArray(daily.weather_code) || daily.weather_code.length !== 7) {
        throw new Error('Incomplete forecast');
      }
      days.replaceChildren(...daily.time.map((date, index) => renderDay(date, index, daily)));
      scrollArea.hidden = false;
      status.hidden = true;
    })
    .catch(() => {
      status.replaceChildren();
      appendTranslations(status, ['Прогноз временно недоступен', 'Prognoz vaqtincha mavjud emas', 'Forecast temporarily unavailable']);
    })
    .finally(() => clearTimeout(timeout));
})();
