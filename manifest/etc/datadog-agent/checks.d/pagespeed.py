'''
Inspired by https://docs.datadoghq.com/developers/agent_checks/
'''
import requests
import time

from checks import AgentCheck

class PageSpeedCheck(AgentCheck):
    def check(self, instance):
        google_api_key = self.init_config.get('google_api_key')
        timeout = self.init_config.get('timeout', 20)

        url = instance['url']
        tags = instance['tags']

        self.log.info('Running pagespeed check for %s' % (url))
        for strategy in ['desktop', 'mobile']:
            try:
                api_url = 'https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=%s&strategy=%s&key=%s' % (url, strategy, google_api_key)

                response = requests.get(api_url, timeout=timeout)
                if response.status_code != 200:
                    self.log.error('Pagespeed API call returned status code %d' % (response.status_code))
                    continue

                try:
                    pagespeed_result = response.json()
                except ValueError as e:
                    self.log.error('Error while decoding JSON response: ' + str(e))
                    continue

                loaded_url = pagespeed_result['id']
                score = pagespeed_result['lighthouseResult']['categories']['performance']['score'] * 100
                percentile_fcp = pagespeed_result['loadingExperience']['metrics']['FIRST_CONTENTFUL_PAINT_MS']['percentile']
                percentile_fid = pagespeed_result['loadingExperience']['metrics']['FIRST_INPUT_DELAY_MS']['percentile']

                metric_tags = ['strategy:' + strategy, 'url:' + loaded_url] + tags
                self.gauge('pagespeed.score', score, tags=metric_tags, hostname=None, device_name=None)
                self.gauge('pagespeed.percentile_fcp', percentile_fcp, tags=metric_tags, hostname=None, device_name=None)
                self.gauge('pagespeed.percentile_fid', percentile_fid, tags=metric_tags, hostname=None, device_name=None)

                self.log.info('Url: %s strategy: %s page score: %d FCP: %d FID %d' % (loaded_url, strategy, score, percentile_fcp, percentile_fid))

                first_contentful_paint  = pagespeed_result['lighthouseResult']['audits']['first-contentful-paint']['numericValue']
                speed_index             = pagespeed_result['lighthouseResult']['audits']['speed-index']['numericValue']
                time_to_interactive     = pagespeed_result['lighthouseResult']['audits']['interactive']['numericValue']
                first_meaningful_paint  = pagespeed_result['lighthouseResult']['audits']['first-meaningful-paint']['numericValue']
                first_cpu_idle          = pagespeed_result['lighthouseResult']['audits']['first-cpu-idle']['numericValue']
                estimated_input_latency = pagespeed_result['lighthouseResult']['audits']['estimated-input-latency']['numericValue']

                self.gauge('pagespeed.first_contentful_paint', first_contentful_paint, tags=metric_tags, hostname=None, device_name=None)
                self.gauge('pagespeed.speed_index', speed_index, tags=metric_tags, hostname=None, device_name=None)
                self.gauge('pagespeed.time_to_interactive', time_to_interactive, tags=metric_tags, hostname=None, device_name=None)
                self.gauge('pagespeed.first_meaningful_paint', first_meaningful_paint, tags=metric_tags, hostname=None, device_name=None)
                self.gauge('pagespeed.first_cpu_idle', first_cpu_idle, tags=metric_tags, hostname=None, device_name=None)
                self.gauge('pagespeed.estimated_input_latency', estimated_input_latency, tags=metric_tags, hostname=None, device_name=None)

            except requests.exceptions.Timeout:
                self.log.error('Pagespeed API call timed out')
