(() => {
  const forecast = document.querySelector('.weather');
  const days = forecast.querySelector('.weather-days');
  const scrollArea = forecast.querySelector('.weather-window');
  const status = forecast.querySelector('.weather-status');
  const languages = ['ru', 'uz', 'en'];
  const formats = languages.map(lang => new Intl.DateTimeFormat(lang, {
    timeZone: 'UTC', weekday: 'short', day: 'numeric', month: 'short',
  }));
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
    appendTranslations(time, index === 0 ? ['Сегодня', 'Bugun', 'Today'] :
      formats.map(format => format.format(new Date(date + 'T00:00:00Z'))));

    const reading = document.createElement('div');
    reading.className = 'weather-reading';
    const condition = conditions.find(([codes]) => codes.includes(daily.weather_code?.[index]));
    if (condition) {
      const [, symbol, description] = condition;
      const icon = document.createElement('span');
      icon.setAttribute('aria-hidden', 'true');
      icon.textContent = symbol;
      const label = document.createElement('span');
      label.className = 'post-share-label';
      appendTranslations(label, description);
      reading.append(icon, label);
    }
    const high = document.createElement('b');
    const low = document.createElement('small');
    high.textContent = Math.round(daily.temperature_2m_max[index]) + '°';
    low.textContent = Math.round(daily.temperature_2m_min[index]) + '°';
    reading.append(high, low);
    day.append(time, reading);

    const precipitation = daily.precipitation_probability_max?.[index];
    if (Number.isFinite(precipitation)) {
      const rain = document.createElement('span');
      rain.className = 'weather-rain';
      appendTranslations(rain, ['Осадки', 'Yog‘in', 'Precip.'].map(label => label + ' ' + precipitation + '%'));
      day.append(rain);
    }
    return day;
  }

  const url = new URL('https://api.open-meteo.com/v1/forecast');
  url.search = new URLSearchParams({
    latitude: '41.3111',
    longitude: '69.2797',
    daily: 'weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max',
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
      if (!Array.isArray(daily?.time) || daily.time.length !== 7 || daily.time.some((date, index) =>
        typeof date !== 'string' || !Number.isFinite(Date.parse(date + 'T00:00:00Z')) ||
        !Number.isFinite(daily.temperature_2m_max?.[index]) || !Number.isFinite(daily.temperature_2m_min?.[index]))) {
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
